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

def integrity_check():
    print("--- DLPC3421 FIRMWARE INTEGRITY CHECK ---")
    
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {port.Name}")
    except:
        print("Error: Could not connect.")
        return

    try:
        # 1. Read Short Status again
        _, status = ReadShortStatus()
        print(f"\n[STATUS]")
        print(f"  App: {status.Application}")
        print(f"  Initialized: {status.SystemInitialized}")
        print(f"  FlashError: {status.FlashError}")
        print(f"  SystemError: {status.SystemError}")

        # 2. Check for Firmware Build Version (if possible in BootApp)
        try:
            _, version = ReadFirmwareBuildVersion()
            print(f"  Firmware Build Version: {version}")
        except:
            print("  Could not read version in BootApp.")

        # 3. Check for specific Flash Update Precheck (if available)
        try:
            # Manually checking for common error registers
            print("\n[DETAILED ERROR LOG]")
            _, log = ReadSystemStatus()
            print(f"  System Status: {log}")
        except Exception as e:
            print(f"  Error reading status: {e}")

        # 4. Attempt a Manual "Execute MainApp" if there is an undocumented register
        # (This is a long shot, but sometimes a software reset is needed)
        print("\nAttempting software reset...")
        WriteExecuteFlashBatchFile(0)
        time.sleep(5)
        
        _, status = ReadShortStatus()
        print(f"  Status after Reset: {status.Application}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        port.Disconnect()
        print("\nIntegrity check complete.")

if __name__ == "__main__":
    integrity_check()
