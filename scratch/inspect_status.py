import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference("DLPComposer.Commands.DLPC342x")
from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command

uart = UARTInterface("UART")
port = next(p for p in uart.GetAvailableInterfaces() if "COM4" in p.Name)
port.Connect()
Command.CommInterface = UARTCommandInterface(port)
_, status = ReadShortStatus()
print(f"Status object members: {dir(status)}")
port.Disconnect()
