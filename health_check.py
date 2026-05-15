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

def check_health():
    print("--- DLPC3421 HARDWARE HEALTH CHECK ---")
    
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
    except:
        print("Error: Could not connect.")
        return

    try:
        # 1. Check Short Status
        _, status = ReadShortStatus()
        print(f"Application: {status.Application}")
        print(f"System Initialized: {status.SystemInitialized}")
        print(f"Fatal Error: {status.FatalError}")
        
        # 2. Check LED Currents (Read back what is actually happening)
        print("\nChecking LED Status...")
        _, r, g, b = ReadRgbLedCurrent()
        print(f"Set LED Currents -> Red: {r}, Green: {g}, Blue: {b}")
        
        # 3. Check Temperatures
        print("\nChecking Temperatures...")
        try:
            _, dmd_temp = ReadDmdTemperature()
            print(f"DMD Temp: {dmd_temp}°C")
        except:
            print("DMD Temp sensor not responding.")
            
        # 4. Check for Light Engine Errors
        print("\nChecking for System Errors...")
        _, sys_errors = ReadSystemError()
        print(f"System Errors: {sys_errors}")

    except Exception as e:
        print(f"Error reading health: {e}")
    finally:
        port.Disconnect()
        print("\nHealth check complete.")

if __name__ == "__main__":
    check_health()
