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

def silent_flash():
    if not os.path.exists(FIRMWARE_PATH):
        print(f"Error: Firmware file not found.")
        return

    print(f"--- STARTING SILENT DLP FLASH ---")
    
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

        print("Initializing EntireFlash Update...")
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)
        
        print("PERFORMING FULL CHIP ERASE (Waiting 60 seconds)...")
        WriteFlashErase()
        for i in range(6):
            time.sleep(10)
            print(f"  Erase progress... {60 - (i+1)*10}s remaining")

        total_blocks = (total_size + BLOCK_SIZE - 1) // BLOCK_SIZE
        print(f"Uploading {total_blocks} blocks (SILENT MODE)...")

        # Start
        first_block = list(data[0:min(BLOCK_SIZE, total_size)])
        WriteFlashStart(first_block)

        for i in range(1, total_blocks):
            start = i * BLOCK_SIZE
            end = min(start + BLOCK_SIZE, total_size)
            chunk = list(data[start:end])
            WriteFlashContinue(chunk)
            
            if i % 100 == 0:
                progress = (i + 1) / total_blocks * 100
                print(f"  Progress: {progress:.1f}% ({i+1}/{total_blocks})")

        print("\nUpload Complete. Waiting for final commit...")
        time.sleep(5)

        print("Rebooting into MainApp...")
        WriteExecuteFlashBatchFile(0)
        time.sleep(10)

        _, status = ReadShortStatus()
        print(f"\n[POST-FLASH STATUS]")
        print(f"  Application: {status.Application}")
        print(f"  Initialized: {status.SystemInitialized}")

        if status.Application.ToString() == "MainApp":
            print("\nSUCCESS! Controller is now in MainApp.")
        else:
            print("\nSTILL IN BOOTAPP. Checking for errors...")
            print(f"  FlashError Flag: {status.FlashError}")

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        port.Disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    silent_flash()
