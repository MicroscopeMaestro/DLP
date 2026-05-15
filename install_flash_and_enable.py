import sys, os, clr, time

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, FlashDataTypeSelect, ImageCurtainEnable, Color as DLPColor, BorderEnable, OperatingMode

FIRMWARE_PATH = r"C:\Users\Juan\Desktop\dlpc34xx_firmware\FWSel_DLPC3421_DLPA2005_pm1_i2c0x36_v1p1p1.img"
PORT_NAME = "COM4"
BLOCK_SIZE = 512

def force_unlock_flash():
    print("--- STARTING FORCE-UNLOCK FLASH ---", flush=True)
    
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if PORT_NAME in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {PORT_NAME}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return

    try:
        # 1. PRE-RESET to clear any latched error states
        print("Resetting controller before flash...", flush=True)
        try: WriteExecuteFlashBatchFile(0)
        except: pass
        time.sleep(5)
        
        # 2. Initialization (using full ENTIRE FLASH range)
        print("Initializing Update (EntireFlash)...", flush=True)
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)
        
        # 3. Targeted Erase
        print("Performing CHIP ERASE (90s wait)...", flush=True)
        WriteFlashErase()
        for i in range(9):
            time.sleep(10)
            print(f"  Erasing... {90 - (i+1)*10}s remaining", flush=True)

        # 4. Final verification of Erase
        print("\nVerifying erase...", flush=True)
        _, d = ReadFlashStart(16)
        print(f"  Flash Header (Should be 255): {list(d)}", flush=True)
        
        if all(b == 255 for b in d):
            print("  ERASE SUCCESSFUL! Starting upload...", flush=True)
        else:
            print("  ERASE FAILED - Flash is still locked at 0x00.", flush=True)
            print("  Continuing anyway to see if writing 0x00 works (Safe for testing)...", flush=True)

        # 5. Upload
        with open(FIRMWARE_PATH, "rb") as f:
            data = f.read()
        total_blocks = (len(data) + BLOCK_SIZE - 1) // BLOCK_SIZE
        print(f"\nUploading {total_blocks} blocks...", flush=True)

        first_block = list(data[0:min(BLOCK_SIZE, len(data))])
        WriteFlashStart(first_block)

        for i in range(1, total_blocks):
            start = i * BLOCK_SIZE
            end = min(start + BLOCK_SIZE, len(data))
            WriteFlashContinue(list(data[start:end]))
            
            if i % 100 == 0:
                # No status checks here to avoid transient errors clearing
                progress = (i + 1) / total_blocks * 100
                print(f"  Progress: {progress:.1f}% ({i+1}/{total_blocks})", flush=True)

        print("\nUpload Complete. Rebooting...", flush=True)
        WriteExecuteFlashBatchFile(0)
        time.sleep(15)

        _, status = ReadShortStatus()
        print(f"Final Status: App={status.Application}", flush=True)

        # 6. Setup LEDs and Enable Light
        print("\n--- ENABLING LIGHT ---", flush=True)
        print("Switching to TestPatternGenerator...", flush=True)
        WriteOperatingModeSelect(OperatingMode.TestPatternGenerator)
        time.sleep(0.5)

        print("Powering on LEDs (Red=300, Green=300, Blue=300)...", flush=True)
        WriteRgbLedCurrent(300, 300, 300)
        WriteRgbLedEnable(True, True, True)
        time.sleep(0.3)

        print("Lifting the Image Curtain...", flush=True)
        WriteDisplayImageCurtain(ImageCurtainEnable.Disable, DLPColor.Black)
        time.sleep(0.3)

        print("Projecting Solid White block...", flush=True)
        WriteSolidField(BorderEnable(0), DLPColor.White)

        print("\nCHECK FOR LIGHT NOW!", flush=True)
        time.sleep(5)

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}", flush=True)
    finally:
        port.Disconnect()
        print("Disconnected.", flush=True)

if __name__ == "__main__":
    force_unlock_flash()
