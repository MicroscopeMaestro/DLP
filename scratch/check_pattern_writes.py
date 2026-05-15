import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
clr.AddReference("DLPComposer.Commands.DLPC347x")
import dlpc347x.commands as cmd

print("Checking for WritePatternData or similar in 347x:")
for name in dir(cmd):
    if "Pattern" in name and "Write" in name:
        print(f" - {name}")
