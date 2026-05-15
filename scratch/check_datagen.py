import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui])
try:
    clr.AddReference("DLPComposer.DataGeneration")
    import DLPComposer.DataGeneration as dg
    print("DataGeneration classes:")
    for name in dir(dg):
        if not name.startswith("__"):
            print(f" - {name}")
except Exception as e:
    print(f"Error: {e}")
