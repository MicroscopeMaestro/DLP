import sys, os, clr
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])
try:
    clr.AddReference("DLPComposer.Commands.DLPC347x")
    import dlpc347x.commands as cmd347x
    print("Found DLPC347x commands!")
    for name in dir(cmd347x):
        if "Pattern" in name:
            print(f" - {name}")
except Exception as e:
    print(f"DLPC347x not found or error: {e}")
