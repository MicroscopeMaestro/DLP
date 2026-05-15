import sys, os, clr, time

# TI Environment Setup
ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, FlashDataTypeSelect

PORT_NAME = "COM4"
FIRMWARE_PATH = r"C:\Users\Juan\Desktop\dlpc34xx_firmware\FWSel_DLPC3421_DLPA2000_pm1_i2c0x36_v1p1p1.img"

def deep_diagnostic():
    print("--- DLPC3421 DEEP HARDWARE OVERLOOK ---", flush=True)
    
    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if PORT_NAME in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {PORT_NAME}", flush=True)
    except Exception as e:
        print(f"Error connecting: {e}", flush=True)
        return

    try:
        # 1. System Status Check
        print("\n[1. System Status]", flush=True)
        _, status = ReadShortStatus()
        print(f"  App State: {status.Application}", flush=True)
        print(f"  System Init: {status.SystemInitialized}", flush=True)
        print(f"  Flash Error: {status.FlashError}", flush=True)
        print(f"  System Error: {status.SystemError}", flush=True)
        
        # 2. Communication Stress Test (Read the same register 100 times)
        print("\n[2. UART Stress Test]", flush=True)
        success_count = 0
        for i in range(100):
            try:
                ReadShortStatus()
                success_count += 1
            except:
                pass
        print(f"  UART Reliability: {success_count}/100 reads successful", flush=True)

        # 3. Flash Memory Map Check (Read first 4KB in small chunks)
        print("\n[3. Flash Read Check]", flush=True)
        try:
            _, data = ReadFlashStart(256)
            print(f"  First 256 bytes read: {list(data[:8])}...", flush=True)
            for i in range(1, 16):
                ReadFlashContinue(256)
            print("  Successfully read first 4KB of flash.", flush=True)
        except Exception as e:
            print(f"  Flash Read Failed: {e}", flush=True)

        # 4. Erase Verification
        print("\n[4. Erase Verification]", flush=True)
        print("  Performing 10s erase of Splash area...", flush=True)
        WriteFlashDataTypeSelect(FlashDataTypeSelect.Splash)
        WriteFlashErase()
        time.sleep(10)
        
        # Read back Splash area (address depends on image, but we just check if it's 0xFF)
        _, d = ReadFlashStart(256)
        print(f"  First 16 bytes after Splash Erase: {list(d[:16])}", flush=True)

        # 5. Reset Check
        print("\n[5. Software Reset Test]", flush=True)
        print("  Requesting Execute Flash Batch File (Reboot)...", flush=True)
        WriteExecuteFlashBatchFile(0)
        print("  Waiting for device to disappear/re-appear...", flush=True)
        time.sleep(5)
        try:
            ReadShortStatus()
            print("  Device is BACK and responding after reset.", flush=True)
        except:
            print("  Device did not respond immediately after reset (Expected if port closed).", flush=True)

    except Exception as e:
        print(f"\nDiagnostic Error: {e}", flush=True)
    finally:
        port.Disconnect()
        print("\nDeep overlook complete.", flush=True)

if __name__ == "__main__":
    deep_diagnostic()
