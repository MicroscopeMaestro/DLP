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

def force_mode_reset():
    print("--- DLPC342x FORCE MODE RESET ---", flush=True)
    
    uart = UARTInterface("UART")
    port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
    port.Connect()
    Command.CommInterface = UARTCommandInterface(port)
    print(f"Connected to {port.Name}", flush=True)
    
    try:
        # 1. Check current state
        _, status = ReadShortStatus()
        print(f"Initial State: App={status.Application}, Init={status.SystemInitialized}", flush=True)
        
        # 2. Force Mode Change (TPG)
        print("Forcing TestPatternGenerator mode...", flush=True)
        WriteOperatingModeSelect(OperatingMode.TestPatternGenerator)
        time.sleep(1.0)
        
        # 3. Explicitly Disable Curtain (The curtain often stays on in External Port mode)
        print("Lifting the Image Curtain...", flush=True)
        WriteDisplayImageCurtain(ImageCurtainEnable.Disable, DLPColor.Black)
        time.sleep(0.5)
        
        # 4. Turn on LEDs
        print("Powering on LEDs...", flush=True)
        WriteRgbLedCurrent(500, 500, 500)
        WriteRgbLedEnable(True, True, True)
        
        # 5. Project White block
        print("Projecting Solid White...", flush=True)
        WriteSolidField(BorderEnable(0), Color.White)
        
        # 6. Final Status Check
        _, status = ReadShortStatus()
        print(f"\nFinal State: App={status.Application}, Init={status.SystemInitialized}", flush=True)
        
        if status.Application.ToString() == "BootApp":
            print("\n!!! RECOVERY FAILED: Controller is stuck in BootApp.", flush=True)
            print("You MUST use the 'Flash Image' tool in the TI GUI to restore firmware.", flush=True)
        else:
            print("\nSUCCESS! Check for light.", flush=True)
            
    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        port.Disconnect()
        print("Disconnected.", flush=True)

if __name__ == "__main__":
    force_mode_reset()
