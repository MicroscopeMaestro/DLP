import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference("DLPComposer.Commands.DLPC342x")
import dlpc342x.commands as cmd

print("Searching for pattern-related commands...")
for name in dir(cmd):
    if "Internal" in name or "Pattern" in name or "Control" in name or "Start" in name:
        print(f" - {name}")
