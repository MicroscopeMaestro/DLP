import sys, os, clr, time

# TI Environment Setup
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, FlashDataTypeSelect

# Configuration
FIRMWARE_PATH = r"C:\Users\Juan\Desktop\dlpc34xx_firmware\FWSel_DLPC3421_DLPA2000_pm1_i2c0x36_v1p1p1.img"
PORT_NAME = "COM4"
BLOCK_SIZE = 1024

def deep_clean_flash():
    if not os.path.exists(FIRMWARE_PATH):
        print(f"Error: Firmware file not found at {FIRMWARE_PATH}")
        return

    print(f"--- STARTING DEEP CLEAN DLP FLASH ---")
    
    # 1. Connect
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if PORT_NAME in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {PORT_NAME}")
    except Exception as e:
        print(f"Error connecting: {e}")
        return

    try:
        with open(FIRMWARE_PATH, "rb") as f:
            data = f.read()
        total_size = len(data)

        # 2. Initialize and DEEP ERASE
        print("Initializing EntireFlash Update...")
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)
        
        print("PERFORMING FULL CHIP ERASE (Waiting 60 seconds)...")
        WriteFlashErase()
        # High-integrity wait for hardware to finish erase
        for i in range(60):
            if i % 10 == 0:
                print(f"  Erasing... {60-i}s remaining")
            time.sleep(1)

        # 3. Upload Data with Error Checking
        total_blocks = (total_size + BLOCK_SIZE - 1) // BLOCK_SIZE
        print(f"Uploading {total_blocks} blocks...")

        # Start
        first_block = list(data[0:min(BLOCK_SIZE, total_size)])
        WriteFlashStart(first_block)

        for i in range(1, total_blocks):
            start = i * BLOCK_SIZE
            end = min(start + BLOCK_SIZE, total_size)
            chunk = list(data[start:end])
            WriteFlashContinue(chunk)
            
            if i % 50 == 0:
                # Check status periodically to ensure no flash errors
                _, status = ReadShortStatus()
                if status.FlashError:
                    print(f"\nCRITICAL: Flash Error detected at block {i}!")
                    return
                
                progress = (i + 1) / total_blocks * 100
                print(f"  Progress: {progress:.1f}% ({i+1}/{total_blocks})")

        print("\nUpload Complete. Verifying...")
        time.sleep(2)

        # 4. Finalize and Reboot
        print("Rebooting into MainApp...")
        WriteExecuteFlashBatchFile(0)
        time.sleep(10) # Wait for reboot

        # 5. Final Verification
        _, status = ReadShortStatus()
        print(f"\n[FINAL STATUS]")
        print(f"  Application: {status.Application}")
        print(f"  Initialized: {status.SystemInitialized}")

        if status.Application.ToString() == "MainApp":
            print("\nSUCCESS! Hardware is now in MainApp. Projector is ready.")
        else:
            print("\nFAILED: Controller is still in BootApp. Firmware may be incompatible.")

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        port.Disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    deep_clean_flash()
