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

def recover_firmware():
    # 1. Path to your desktop image
    img_path = r"C:\Users\Juan\Desktop\dlpc34xx_firmware\FWSel_DLPC3421_DLPA2000_pm1_i2c0x36_v1p1p1.img"
    
    if not os.path.exists(img_path):
        print(f"Error: Firmware file not found at {img_path}")
        return

    print(f"--- DLPC3421 FIRMWARE RECOVERY ---")
    print(f"File: {os.path.basename(img_path)}")
    
    # 2. Connect
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {port.Name}")
    except StopIteration:
        print("Error: COM4 not found. Is the device plugged in?")
        return

    try:
        # 3. Read image data
        with open(img_path, "rb") as f:
            data = f.read()
        
        print(f"Image Size: {len(data)} bytes")
        
        # 4. Initialize Flash Update
        print("Initializing Flash Update (EntireFlash)...")
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)
        # WriteFlashDataLength is only for small chunks < 64KB. 
        # For EntireFlash, the stream length is handled by the protocol.
        
        print("Erasing Flash... (This may take 30 seconds)")
        WriteFlashErase()
        time.sleep(2) # Give it a moment to start
        
        # 5. Write Data in chunks (TI DLL usually handles chunks if we pass the whole array)
        # But we'll do it safely in blocks of 1024
        block_size = 1024
        total_blocks = (len(data) + block_size - 1) // block_size
        
        print(f"Writing {total_blocks} blocks...")
        
        # Write first block
        first_block = data[0:block_size]
        WriteFlashStart(list(first_block))
        
        # Write remaining blocks
        for i in range(1, total_blocks):
            start = i * block_size
            end = min(start + block_size, len(data))
            chunk = data[start:end]
            WriteFlashContinue(list(chunk))
            
            if i % 100 == 0:
                print(f"  Progress: {i}/{total_blocks} blocks...")

        print("\nFlash Write Complete!")
        print("Rebooting device...")
        WriteExecuteFlashBatchFile(0)
        
        print("\nRECOVERY FINISHED. Wait 10 seconds and check for light/logo.")

    except Exception as e:
        print(f"Error during flash: {e}")
    finally:
        port.Disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    recover_firmware()
