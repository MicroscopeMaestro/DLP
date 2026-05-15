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

PORT_NAME = "COM5"

def verify_erase():
    print(f"--- VERIFYING FLASH ERASE ---", flush=True)
    
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
        # 1. Erase
        print("Initializing EntireFlash Update...", flush=True)
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)
        
        print("PERFORMING FULL CHIP ERASE (90s)...", flush=True)
        WriteFlashErase()
        time.sleep(90)
        
        # 2. Read back a few blocks to check for 0xFF
        print("Reading back start of flash...", flush=True)
        # ReadFlashStart requires a Length argument
        _, data = ReadFlashStart(1024)
        print(f"Block 0 Start bytes: {list(data[:16])}", flush=True)
        
        if all(b == 255 for b in data[:16]):
            print("SUCCESS: Flash seems erased (found 0xFF).", flush=True)
        else:
            print("WARNING: Flash is NOT erased. Still contains data.", flush=True)

    except Exception as e:
        print(f"\nERROR: {e}", flush=True)
    finally:
        port.Disconnect()
        print("Disconnected.", flush=True)

if __name__ == "__main__":
    verify_erase()
