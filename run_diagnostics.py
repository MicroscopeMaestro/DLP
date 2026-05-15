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

def run_diagnostics():
    print("--- DLPC3421 HARDWARE DIAGNOSTICS ---")
    
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {port.Name}")
    except:
        print("Error: Could not connect to COM4.")
        return

    try:
        # 1. Check Application Mode
        _, status = ReadShortStatus()
        print(f"\n[SYSTEM STATUS]")
        print(f"  Application: {status.Application}")
        print(f"  Initialized: {status.SystemInitialized}")
        print(f"  Fatal Error: {status.FatalError}")
        
        # 2. Check Operating Mode
        _, mode = ReadOperatingModeSelect()
        print(f"  Current Operating Mode: {mode}")

        # 3. Check LEDs
        _, r_en, g_en, b_en = ReadRgbLedEnable()
        _, r_cur, g_cur, b_cur = ReadRgbLedCurrent()
        print(f"\n[LED STATUS]")
        print(f"  Enabled -> R:{r_en}, G:{g_en}, B:{b_en}")
        print(f"  Current -> R:{r_cur}, G:{g_cur}, B:{b_cur}")

        # 4. Check Curtain
        _, curtain, color = ReadDisplayImageCurtain()
        print(f"\n[IMAGE CURTAIN]")
        print(f"  Curtain State: {curtain} (Should be Disable for light)")

        # 5. Check for specific errors
        _, sys_error = ReadSystemError()
        print(f"\n[ERRORS]")
        print(f"  System Error Code: {sys_error}")
        
        if status.Application.ToString() == "BootApp":
            print("\nWARNING: Device is stuck in BootApp. The firmware might not be valid or was not executed.")

    except Exception as e:
        print(f"Error during diagnostics: {e}")
    finally:
        port.Disconnect()
        print("\nDiagnostics complete.")

if __name__ == "__main__":
    run_diagnostics()
