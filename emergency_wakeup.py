import sys
import os
import clr
import time

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
ti_scripts = os.path.join(ti_gui, "Settings", "Scripts")
sys.path.append(ti_gui)
sys.path.append(ti_scripts)

clr.AddReference(os.path.join(ti_gui, "DLPComposer.Commands.DLPC342x.dll"))
clr.AddReference(os.path.join(ti_gui, "DLPComposer.IO.dll"))

from dlpc342x.commands import *
import DLPComposer.IO
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command

def wake_up():
    print("Attempting Emergency Wake-up...", flush=True)
    
    uart_iface = UARTInterface("UART")
    target_port = None
    for port in uart_iface.GetAvailableInterfaces():
        if "COM4" in port.Name:
            target_port = port
            break
            
    if not target_port: return
        
    target_port.Connect()
    Command.CommInterface = UARTCommandInterface(target_port)
    
    try:
        # 1. Force Mode
        print("Switching to Test Pattern Mode...", flush=True)
        WriteOperatingModeSelect(OperatingMode.TestPatternGenerator)
        time.sleep(1.0)
        
        # 2. Force LEDs
        print("Enabling LEDs and Current...", flush=True)
        WriteRgbLedEnable(True, True, True)
        WriteRgbLedCurrent(500, 500, 500)
        
        # 3. Unfreeze/Uncurtain
        WriteImageFreeze(False)
        WriteDisplayImageCurtain(ImageCurtainEnable.Disable, Color.Black)
        
        # 4. Display a pattern
        from DLPComposer.Commands.DLPC342x import BorderEnable
        print("Triggering Checkerboard...", flush=True)
        WriteCheckerboard(BorderEnable.Disable, Color.Black, Color.White, 8, 8)
        
        time.sleep(2.0)
        _, s = ReadShortStatus()
        print(f"Status after wake-up: App={s.Application}, Init={s.SystemInitialized}", flush=True)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        target_port.Disconnect()

if __name__ == "__main__":
    wake_up()
