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

def run_diagnostic():
    print("--- DLPC3430 Hardware Health Check ---", flush=True)
    
    # 1. Connect
    uart_iface = UARTInterface("UART")
    target_port = None
    for port in uart_iface.GetAvailableInterfaces():
        if "COM4" in port.Name:
            target_port = port
            break
            
    if not target_port:
        print("Error: COM4 not found.", flush=True)
        return
        
    target_port.Connect()
    Command.CommInterface = UARTCommandInterface(target_port)
    print(f"Connected to {target_port.Name}.", flush=True)
    
    # 2. Read State
    try:
        _, mode = ReadOperatingModeSelect()
        print(f"Operating Mode: {mode}", flush=True)
        
        _, r, g, b = ReadRgbLedCurrent()
        print(f"LED Currents: R={r}, G={g}, B={b}", flush=True)
        
        _, freeze = ReadImageFreeze()
        print(f"Image Frozen: {freeze}", flush=True)
        
        _, curtain_en, curtain_col = ReadDisplayImageCurtain()
        print(f"Curtain: Enabled={curtain_en}, Color={curtain_col}", flush=True)
        
        _, sys_status = ReadSystemStatus()
        print(f"System Status: {sys_status}", flush=True)
        
        _, short_status = ReadShortStatus()
        print(f"Short Status: {short_status}", flush=True)
        
        # 3. Attempt Fix (Force LEDs On)
        if r == 0 and g == 0 and b == 0:
            print("\n!!! LEDs are OFF. Attempting to force them ON...", flush=True)
            WriteRgbLedCurrent(500, 500, 500) # Safe default
            WriteRgbLedEnable(True, True, True)
            print("Set LED currents to 500. Check device now.", flush=True)
            
        if freeze:
            print("Unfreezing image...", flush=True)
            WriteImageFreeze(False)
            
    except Exception as e:
        print(f"Diagnostic Error: {e}", flush=True)
    finally:
        target_port.Disconnect()
        print("\nDisconnected.", flush=True)

if __name__ == "__main__":
    run_diagnostic()
