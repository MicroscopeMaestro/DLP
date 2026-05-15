import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui])
try:
    clr.AddReference("DLPComposer.FlashDataStructures")
    import DLPComposer.FlashDataStructures as fds
    print("FlashDataStructures classes:")
    for name in dir(fds):
        if not name.startswith("__"):
            print(f" - {name}")
except Exception as e:
    print(f"Error: {e}")
