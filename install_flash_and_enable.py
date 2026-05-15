import sys, os, clr, time

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, FlashDataTypeSelect, ImageCurtainEnable, Color as DLPColor, BorderEnable

FIRMWARE_PATH = r"C:\Users\Juan\Desktop\dlpc34xx_firmware\FWSel_DLPC3421_DLPA2005_pm1_i2c0x36_v1p1p1.img"
PORT_NAME = "COM4"

def remote_software_recovery():
    print("--- STARTING REMOTE-ONLY SOFTWARE RECOVERY ---", flush=True)
    
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
        # 1. Trigger "Soft-Hard" Reset by pulsing the bridge
        print("Pulsing UART bridge to trigger MSPM0 reset sequence...", flush=True)
        # We try to toggle the DTR/RTS which on some TI boards is tied to PROJ_ON/RESET
        try:
            port.BasePort.DtrEnable = True
            time.sleep(0.5)
            port.BasePort.DtrEnable = False
            time.sleep(1.0)
        except: pass

        # 2. Force the controller to "Ready" state
        print("Readying flash engine...", flush=True)
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)
        
        # 3. VERIFY READ (Checking if 0x00 is persistent)
        _, d = ReadFlashStart(16)
        print(f"Current Flash Header: {list(d)}", flush=True)

        # 4. If all zeros, try a "Format-Erase" loop
        if all(b == 0 for b in d):
            print("Detected 0x00 Lock. Attempting to force bit-flip...", flush=True)
            # We try to write 0xFF without an erase to see if the bits are actually 0xFF but reading 0
            try:
                WriteFlashStart([255]*512)
                time.sleep(1)
                _, d2 = ReadFlashStart(16)
                print(f"Header after 0xFF write attempt: {list(d2)}", flush=True)
            except: pass

        # 5. Full Erase + Upload
        print("\nStarting Deep Chip Erase (90s)...", flush=True)
        WriteFlashErase()
        for i in range(9):
            time.sleep(10)
            print(f"  Erasing... {90 - (i+1)*10}s remaining", flush=True)

        print("\nStarting Upload (512B blocks)...", flush=True)
        with open(FIRMWARE_PATH, "rb") as f:
            data = f.read()
        
        WriteFlashStart(list(data[0:512]))
        for i in range(1, (len(data)+511)//512):
            WriteFlashContinue(list(data[i*512:min((i+1)*512, len(data))]))
            if i % 500 == 0:
                print(f"  Progress: {i*512/len(data)*100:.1f}%", flush=True)

        print("\nUpload complete. Triggering MainApp jump...", flush=True)
        WriteExecuteFlashBatchFile(0)
        time.sleep(5)
        
        _, s = ReadShortStatus()
        print(f"Final Status: App={s.Application}", flush=True)

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
        print(f"Error: {e}", flush=True)
    finally:
        port.Disconnect()
        print("Disconnected.", flush=True)

if __name__ == "__main__":
    remote_software_recovery()
