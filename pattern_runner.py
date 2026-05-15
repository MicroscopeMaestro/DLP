import sys, os, clr

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference(os.path.join(ti_gui, "DLPComposer.Commands.DLPC342x.dll"))
clr.AddReference(os.path.join(ti_gui, "DLPComposer.IO.dll"))

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, BorderEnable
import time

# UART Setup
_uart = UARTInterface("UART")
_port = next(p for p in _uart.GetAvailableInterfaces() if "COM4" in p.Name)
_port.Connect()
Command.CommInterface = UARTCommandInterface(_port)
print("Connected to COM4", flush=True)

# This script is designed to run INSIDE the TI EVM GUI Script Runner.
# The GUI handles device initialization automatically.

display_time = 2

print("Setting up TestPatternGenerator mode...", flush=True)
WriteOperatingModeSelect(OperatingMode.TestPatternGenerator)
time.sleep(0.5)

# CRITICAL: Lift the image curtain (blocks light until explicitly removed)
from DLPComposer.Commands.DLPC342x import ImageCurtainEnable, Color as DLPColor
WriteDisplayImageCurtain(ImageCurtainEnable.Disable, DLPColor.Black)
time.sleep(0.3)

# Solid White - basic sanity check
print("Projecting Solid White...", flush=True)
WriteSolidField(BorderEnable(0), Color.White)
time.sleep(display_time)

# Horizontal gratings
print("Horizontal gratings...", flush=True)
for spacing in [2, 4, 8, 16, 32]:
    WriteHorizontalLines(BorderEnable(0), Color.White, Color.Black, spacing, spacing)
    time.sleep(display_time)

# Vertical gratings
print("Vertical gratings...", flush=True)
for spacing in [2, 4, 8, 16, 32]:
    WriteVerticalLines(BorderEnable(0), Color.White, Color.Black, spacing, spacing)
    time.sleep(display_time)

# Checkerboard
print("Checkerboard...", flush=True)
for count in [4, 8, 16, 32]:
    WriteCheckerboard(BorderEnable(0), Color.Black, Color.White, count, count)
    time.sleep(display_time)

_port.Disconnect()
print("Done.", flush=True)
