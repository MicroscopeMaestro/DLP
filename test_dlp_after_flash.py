import sys, os, clr, time

# TI Environment Setup
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.Commands.DLPC347x")
clr.AddReference("DLPComposer.IO")

import dlpc342x.commands as cmd21
import dlpc347x.commands as cmd7x
from DLPComposer.Commands.DLPC342x import Command as Command21, ImageCurtainEnable, Color as DLPColor
from DLPComposer.Commands.DLPC347x import Command as Command7x
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface

def post_flash_test():
    print("--- DLPC3421 POST-FLASH LIGHT TEST ---")
    
    # 1. Connect
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
        port.Connect()
        comm = UARTCommandInterface(port)
        Command21.CommInterface = comm
        Command7x.CommInterface = comm
        print(f"Connected to {port.Name}")
    except:
        print("Error: Could not connect to COM4.")
        return

    try:
        # 2. Power on LEDs
        print("Powering on LEDs (R=500, G=500, B=500)...")
        cmd21.WriteRgbLedCurrent(500, 500, 500)
        cmd21.WriteRgbLedEnable(True, True, True)
        time.sleep(0.5)

        # 3. Lift the Curtain
        print("Lifting Image Curtain...")
        cmd21.WriteDisplayImageCurtain(ImageCurtainEnable.Disable, DLPColor.Black)
        time.sleep(0.5)

        # 4. Display Initial Splash Image
        print("Displaying Splash Image (Index 0)...")
        cmd21.WriteOperatingModeSelect(cmd21.OperatingMode.SplashScreen)
        cmd21.WriteSplashScreenSelect(0)
        cmd21.WriteSplashScreenExecute()
        time.sleep(3)

        # 5. Run the Fringes (Internal Patterns)
        print("Switching to Fringes (Internal Patterns)...")
        cmd21.WriteOperatingModeSelect(cmd21.OperatingMode.SensInternalPattern)
        time.sleep(0.5)
        
        print("Starting Pattern Sequence...")
        cmd7x.WriteInternalPatternControl(cmd7x.PatternControl.Start, 0xFF)
        
        print("\nSUCCESS! Check your DLP. You should see fringes running now.")
        time.sleep(10)

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        port.Disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    post_flash_test()
