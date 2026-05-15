import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui])
clr.AddReference("DLPComposer.Commands.DLPC342x")
import DLPComposer
print(f"DLPComposer: {dir(DLPComposer)}")
if hasattr(DLPComposer, "FlashDataStructures"):
    print(f"FlashDataStructures: {dir(DLPComposer.FlashDataStructures)}")
