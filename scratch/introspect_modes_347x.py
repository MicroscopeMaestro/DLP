import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference("DLPComposer.Commands.DLPC347x")
from dlpc347x.commands import OperatingMode
print("OperatingMode values for 347x:")
for name in dir(OperatingMode):
    if not name.startswith("__"):
        print(f" - {name}")
