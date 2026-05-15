import sys, os, clr, time

# TI Environment Setup
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

# References for both 342x and 347x (Structured Light)
clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.Commands.DLPC347x")
clr.AddReference("DLPComposer.IO")

import dlpc342x.commands as cmd21
import dlpc347x.commands as cmd7x
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command as Command21, ImageCurtainEnable, Color as DLPColor
from DLPComposer.Commands.DLPC347x import Command as Command7x

def run_dlp_sequence():
    print("--- DLP FLASH CONTENT RUNNER ---")
    
    # 1. Connect
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
        port.Connect()
        # The underlying interface must be shared across both command libraries
        comm = UARTCommandInterface(port)
        Command21.CommInterface = comm
        Command7x.CommInterface = comm
        print(f"Connected to {port.Name}")
    except StopIteration:
        print("Error: COM4 not found.")
        return

    try:
        # 2. Lift the curtain (standard for any projection)
        print("Lifting Image Curtain...")
        cmd21.WriteDisplayImageCurtain(ImageCurtainEnable.Disable, DLPColor.Black)
        time.sleep(0.5)

        # 3. DISPLAY IMAGE (Splash Screen)
        print("\nStep 1: Displaying Splash Image...")
        # Select splash index 0
        cmd21.WriteSplashScreenSelect(0)
        # Set mode to SplashScreen
        cmd21.WriteOperatingModeSelect(cmd21.OperatingMode.SplashScreen)
        # Execute (actually show it)
        cmd21.WriteSplashScreenExecute()
        
        print("Showing image for 5 seconds...")
        time.sleep(5)

        # 4. RUN FRINGES (Internal Patterns)
        print("\nStep 2: Running Fringes (Internal Patterns)...")
        # Set mode to Internal Pattern (Structured Light)
        # Note: cmd21.OperatingMode.SensInternalPattern is usually the correct one for 3421/347x
        cmd21.WriteOperatingModeSelect(cmd21.OperatingMode.SensInternalPattern)
        time.sleep(0.5)
        
        # Start the sequence
        # cmd7x.PatternControl.Start = 0
        # 0xFF usually means loop forever or until stopped
        print("Starting Pattern Sequence...")
        cmd7x.WriteInternalPatternControl(cmd7x.PatternControl.Start, 0xFF)
        
        print("Fringes are now running. Press Ctrl+C to stop (in your mind) or wait 10 seconds.")
        time.sleep(10)
        
        # Optionally stop
        # print("Stopping Fringes...")
        # cmd7x.WriteInternalPatternControl(cmd7x.PatternControl.Stop, 0)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        port.Disconnect()
        print("\nDisconnected.")

if __name__ == "__main__":
    run_dlp_sequence()
