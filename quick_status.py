import sys, os, clr, time

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command

PORT_NAME = "COM4"

def quick_status():
    print("--- POST-POWER-CYCLE DEVICE STATUS ---", flush=True)

    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if PORT_NAME in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {PORT_NAME}", flush=True)
    except Exception as e:
        print(f"Connection Error: {e}", flush=True)
        return

    try:
        # Short status
        _, st = ReadShortStatus()
        print(f"\n[SHORT STATUS]", flush=True)
        print(f"  Application : {st.Application}", flush=True)
        print(f"  Initialized : {st.SystemInitialized}", flush=True)
        print(f"  FlashError  : {st.FlashError}", flush=True)
        print(f"  SystemError : {st.SystemError}", flush=True)

        # Firmware version (works in both BootApp and MainApp)
        try:
            result = ReadFirmwareBuildVersion()
            # Returns (ExecutionSummary, major, minor, patch)
            summary, major, minor, patch = result
            print(f"\n[FIRMWARE VERSION]", flush=True)
            print(f"  {major}.{minor}.{patch}", flush=True)
        except Exception as e:
            print(f"\n[FIRMWARE VERSION] Not available: {e}", flush=True)

        # Flash update precheck — tells us if a flash write is even allowed
        try:
            # Pass total firmware size as the expected package size
            fw_size = os.path.getsize(r"C:\Users\Juan\Desktop\dlpc34xx_firmware\FWSel_DLPC3421_DLPA2000_pm1_i2c0x36_v1p1p1.img")
            result = ReadFlashUpdatePrecheck(fw_size)
            print(f"\n[FLASH PRECHECK] (fw_size={fw_size})", flush=True)
            print(f"  {result}", flush=True)
        except Exception as e:
            print(f"\n[FLASH PRECHECK] Error: {e}", flush=True)

        # System status register
        try:
            result = ReadSystemStatus()
            print(f"\n[SYSTEM STATUS]", flush=True)
            print(f"  {result}", flush=True)
        except Exception as e:
            print(f"\n[SYSTEM STATUS] Error: {e}", flush=True)

    except Exception as e:
        print(f"\nError: {e}", flush=True)
    finally:
        port.Disconnect()
        print("\nDisconnected.", flush=True)

if __name__ == "__main__":
    quick_status()
