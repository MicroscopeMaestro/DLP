import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui])
clr.AddReference("DLPComposer.Splash")
import DLPComposer.Splash as splash

print("Splash related classes:")
for name in dir(splash):
    if not name.startswith("__"):
        print(f" - {name}")
