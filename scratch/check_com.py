import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference("DLPComposer.IO")
from DLPComposer.IO import UARTInterface
uart = UARTInterface("UART")
interfaces = list(uart.GetAvailableInterfaces())
print(f"Available interfaces: {[p.Name for p in interfaces]}")
