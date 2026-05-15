import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference("DLPComposer.Commands.DLPC342x")
from dlpc342x.commands import *

def print_enum(enum_type):
    print(f"\n{enum_type.__name__} values:")
    for name in dir(enum_type):
        if not name.startswith("__") and not name.islower():
            print(f" - {name}")

print_enum(PatternControl)
print_enum(PatternConfiguration)
