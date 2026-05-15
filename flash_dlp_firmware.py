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

def flash_dlp():
    if not os.path.exists(FIRMWARE_PATH):
        print(f"Error: Firmware file not found at {FIRMWARE_PATH}")
        return

    print(f"--- STARTING DLP FIRMWARE FLASH ---")
    print(f"Target File: {os.path.basename(FIRMWARE_PATH)}")
    
    # 1. Connect
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if PORT_NAME in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {PORT_NAME}")
    except StopIteration:
        print(f"Error: {PORT_NAME} not found. Please check connection.")
        return
    except Exception as e:
        print(f"Error connecting: {e}")
        return

    try:
        # 2. Prepare Data
        with open(FIRMWARE_PATH, "rb") as f:
            data = f.read()
        total_size = len(data)
        print(f"Firmware Size: {total_size} bytes")

        # 3. Initialize Flash
        print("Initializing Flash Update (EntireFlash)...")
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)
        
        print("Erasing Flash... (Please wait)")
        WriteFlashErase()
        time.sleep(3) # Initial wait for erase cycle to stabilize

        # 4. Upload Data
        total_blocks = (total_size + BLOCK_SIZE - 1) // BLOCK_SIZE
        print(f"Uploading {total_blocks} blocks...")

        # Write first block
        first_block = list(data[0:min(BLOCK_SIZE, total_size)])
        WriteFlashStart(first_block)

        # Write remaining blocks
        for i in range(1, total_blocks):
            start = i * BLOCK_SIZE
            end = min(start + BLOCK_SIZE, total_size)
            chunk = list(data[start:end])
            WriteFlashContinue(chunk)
            
            if i % 20 == 0 or i == total_blocks - 1:
                progress = (i + 1) / total_blocks * 100
                print(f"  Progress: {progress:.1f}% ({i+1}/{total_blocks})")

        print("\nFlash Write Successful!")
        
        # 5. Execute and Reboot
        print("Finalizing flash and rebooting device...")
        WriteExecuteFlashBatchFile(0)
        
        print("\nSUCCESS! The DLP should now reboot. Wait ~10 seconds for it to initialize.")

    except Exception as e:
        print(f"\nCRITICAL ERROR DURING FLASH: {e}")
        print("Device may be in an unstable state. Try running the flash again.")
    finally:
        port.Disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    flash_dlp()
