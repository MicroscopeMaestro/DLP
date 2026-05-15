import sys, os, clr, time

# TI Environment Setup
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, BorderEnable, ImageCurtainEnable, Color as DLPColor

def final_test():
    print("--- DLPC3421 FINAL LIGHT TEST ---")
    
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
        # 1. Switch to Test Pattern mode
        print("Switching to TestPatternGenerator...")
        WriteOperatingModeSelect(OperatingMode.TestPatternGenerator)
        time.sleep(0.5)

        # 2. Setup LEDs (This is the missing step!)
        print("Powering on LEDs (Red=300, Green=300, Blue=300)...")
        WriteRgbLedCurrent(300, 300, 300)
        WriteRgbLedEnable(True, True, True)
        time.sleep(0.3)

        # 3. Lift the Curtain
        print("Lifting the Image Curtain...")
        WriteDisplayImageCurtain(ImageCurtainEnable.Disable, DLPColor.Black)
        time.sleep(0.3)

        # 4. Project Solid White
        print("Projecting Solid White block...")
        WriteSolidField(BorderEnable(0), Color.White)
        
        print("\nCHECK FOR LIGHT NOW!")
        time.sleep(5) # Keep it on for 5 seconds

    except Exception as e:
        print(f"Error: {e}")
    finally:
        port.Disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    final_test()
