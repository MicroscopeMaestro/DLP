import sys, os, clr, time

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, FlashDataTypeSelect

PORT_NAME = "COM4"

def test_erases():
    print("--- TESTING DIFFERENT ERASE TYPES ---", flush=True)
    
    uart = UARTInterface("UART")
    port = next(p for p in uart.GetAvailableInterfaces() if PORT_NAME in p.Name)
    port.Connect()
    Command.CommInterface = UARTCommandInterface(port)
    print(f"Connected to {PORT_NAME}", flush=True)

    types_to_test = [
        FlashDataTypeSelect.Splash,
        FlashDataTypeSelect.MainApp,
        FlashDataTypeSelect.EntireFlashNoOem,
        FlashDataTypeSelect.EntireFlash
    ]

    try:
        for t in types_to_test:
            print(f"\nTesting Erase for: {t}", flush=True)
            WriteFlashDataTypeSelect(t)
            WriteFlashErase()
            time.sleep(5) # Brief wait
            
            # Read back first 16 bytes
            _, d = ReadFlashStart(16)
            print(f"  First 16 bytes: {list(d)}", flush=True)
            
            if all(b == 255 for b in d):
                print(f"  ✅ SUCCESS for {t}!", flush=True)
            else:
                print(f"  ❌ FAILED for {t}.", flush=True)

    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        port.Disconnect()
        print("\nTest complete.", flush=True)

if __name__ == "__main__":
    test_erases()
