import sys, os, clr, time

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.Commands.DLPC342x")
clr.AddReference("DLPComposer.IO")

from dlpc342x.commands import *
from DLPComposer.IO import UARTInterface
from DLPComposer.IO.DLPC34xx import UARTCommandInterface
from DLPComposer.Commands.DLPC342x import Command, FlashDataTypeSelect

FIRMWARE_PATH = r"C:\Users\Juan\Desktop\dlpc34xx_firmware\FWSel_DLPC3421_DLPA2000_pm1_i2c0x36_v1p1p1.img"
PORT_NAME = "COM4"
BLOCK_SIZE = 256

def probe_flash_write():
    """
    Probes the flash write to determine WHEN exactly the FlashError flag first
    gets set, and what the full status registers say at that moment.
    """
    print("--- FLASH WRITE PROBE ---", flush=True)

    uart = UARTInterface("UART")
    try:
        port = next(p for p in uart.GetAvailableInterfaces() if PORT_NAME in p.Name)
        port.Connect()
        Command.CommInterface = UARTCommandInterface(port)
        print(f"Connected to {PORT_NAME}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return

    try:
        with open(FIRMWARE_PATH, "rb") as f:
            data = f.read()

        print("Initializing EntireFlash Update...", flush=True)
        WriteFlashDataTypeSelect(FlashDataTypeSelect.EntireFlash)

        print("Erasing (60s)...", flush=True)
        WriteFlashErase()
        time.sleep(60)
        print("Erase done.", flush=True)

        total_blocks = (len(data) + BLOCK_SIZE - 1) // BLOCK_SIZE
        print(f"Writing {total_blocks} blocks, checking EVERY block...", flush=True)

        first_block = list(data[0:min(BLOCK_SIZE, len(data))])
        WriteFlashStart(first_block)

        error_found_at = None
        for i in range(1, min(250, total_blocks)):  # Only go to block 250 to find exact failure point
            start = i * BLOCK_SIZE
            end = min(start + BLOCK_SIZE, len(data))
            chunk = list(data[start:end])

            WriteFlashContinue(chunk)

            # Check EVERY block
            _, s = ReadShortStatus()
            if s.FlashError.ToString() != "NoError":
                error_found_at = i
                print(f"\n!!! FLASH ERROR FIRST SEEN AT BLOCK {i} !!!", flush=True)
                print(f"  FlashError  : {s.FlashError}", flush=True)
                print(f"  SystemError : {s.SystemError}", flush=True)
                print(f"  CommError   : {s.CommunicationError}", flush=True)
                print(f"  Application : {s.Application}", flush=True)
                print(f"  Data offset : {i * BLOCK_SIZE} bytes ({i * BLOCK_SIZE / 1024:.1f} KB) into file", flush=True)
                
                # Check a few blocks after to see if it recovers
                for j in range(3):
                    time.sleep(0.5)
                    _, s2 = ReadShortStatus()
                    print(f"  [+{j+1}s] FlashError={s2.FlashError}, App={s2.Application}", flush=True)
                break

        if error_found_at is None:
            print(f"\nNo error in first 250 blocks — something else is happening!", flush=True)

    except Exception as e:
        print(f"\nException: {e}", flush=True)
    finally:
        port.Disconnect()
        print("\nDisconnected.", flush=True)

if __name__ == "__main__":
    probe_flash_write()
