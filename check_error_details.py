import sys, os, clr, time

# TI Environment Setup
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command

def check_error_details():
    print("--- INVESTIGATING FLASH ERROR DETAILS ---")
    
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if "COM5" in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {port.Name}")
    except:
        print("Error: Could not connect.")
        return

    try:
        # Check Short Status for specific error flags
        _, status = ReadShortStatus()
        print(f"\n[SHORT STATUS]")
        print(f"  FlashError: {status.FlashError}")
        print(f"  SystemError: {status.SystemError}")
        print(f"  CommunicationError: {status.CommunicationError}")

        # Check for detailed System Error
        _, sys_error = ReadSystemError()
        print(f"\n[SYSTEM ERROR CODE]")
        print(f"  Error: {sys_error}")

        # Check specifically for Flash related registers if any (Internal registers)
        # 0x0C is often a status register on some 34xx variants
        # but let's stick to the high-level commands first

    except Exception as e:
        print(f"Error reading details: {e}")
    finally:
        port.Disconnect()
        print("\nInvestigation complete.")

if __name__ == "__main__":
    check_error_details()
