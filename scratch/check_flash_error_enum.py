import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference("DLPComposer.Commands.DLPC342x")
from dlpc342x.commands import FlashError
print("FlashError enum values:")
for name in dir(FlashError):
    if not name.startswith("__"):
        print(f" - {name}")
