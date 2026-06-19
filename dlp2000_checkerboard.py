#!/usr/bin/env python3
"""
DLPC3430 checkerboard test pattern via I2C.
Ref: DLPC3430 Host Controller Programmer's Guide.

Command 0x1A = TestPatternSelect
  [Enable, Pattern, BitDepth, PatternColor]
  Pattern 0x04 = Checkerboard

Run BEFORE display init to confirm I2C writes reach the hardware.
"""

import sys
import time
import smbus2

I2C_BUS = 4
DLPC3430_ADDR = 0x1B


def wr(bus, cmd, data):
    bus.write_i2c_block_data(DLPC3430_ADDR, cmd, data)


def rd(bus, cmd, n, delay_ms=50):
    w = smbus2.i2c_msg.write(DLPC3430_ADDR, [cmd])
    bus.i2c_rdwr(w)
    time.sleep(delay_ms / 1000)
    r = smbus2.i2c_msg.read(DLPC3430_ADDR, n)
    bus.i2c_rdwr(r)
    return list(r)


def read_status(bus):
    print("\n--- Status ---")
    for cmd, n, name in [
        (0x02, 1, "ShortStatus"),
        (0x03, 5, "SystemStatus"),
        (0x05, 8, "FirmwareTag"),
        (0x06, 3, "SoftwareVersion"),
    ]:
        try:
            d = rd(bus, cmd, n)
            if name == "FirmwareTag":
                print(f"  {name} (0x{cmd:02X}): {bytes(d).decode('ascii', errors='replace')!r} {[hex(x) for x in d]}")
            else:
                print(f"  {name} (0x{cmd:02X}): {[hex(x) for x in d]}")
        except Exception as e:
            print(f"  {name} (0x{cmd:02X}): ERROR {e}")


def display_init(bus):
    print("\n--- Display Init ---")
    # InputSignalModeSelect (0x0C): nHD 640x360
    wr(bus, 0x0C, [0x00, 0x00, 0x00, 0x1B])
    print("  [1] InputSignalMode: nHD 640x360")
    time.sleep(0.1)

    # DisplayImageControl (0x0B): parallel RGB, enable
    wr(bus, 0x0B, [0x00, 0x00, 0x00, 0x00])
    print("  [2] DisplayImageControl: parallel mode")
    time.sleep(0.1)


def checkerboard(bus):
    print("\n--- Test Pattern: Checkerboard ---")
    # TestPatternSelect (0x1A):
    #   Byte0: Enable (1=on)
    #   Byte1: Pattern (4=checkerboard)
    #   Byte2: BitDepth (2=8-bit)
    #   Byte3: PatternColor (0=white)
    wr(bus, 0x1A, [0x01, 0x04, 0x02, 0x00])
    print("  Sent 0x1A [01 04 02 00] — checkerboard enabled")


def solid_white(bus):
    print("\n--- Test Pattern: Solid White ---")
    # Pattern 0=Solid field, PatternColor 0xFF=white
    wr(bus, 0x1A, [0x01, 0x00, 0x02, 0xFF])
    print("  Sent 0x1A [01 00 02 FF] — solid white")


def solid_black(bus):
    print("\n--- Test Pattern: Solid Black ---")
    wr(bus, 0x1A, [0x01, 0x01, 0x02, 0x00])
    print("  Sent 0x1A [01 01 02 00] — solid black")


def pattern_off(bus):
    print("\n--- Test Pattern: Off (normal input) ---")
    wr(bus, 0x1A, [0x00, 0x00, 0x02, 0x00])
    print("  Sent 0x1A [00 00 02 00] — test pattern disabled")


def main():
    print(f"DLPC3430 Checkerboard Test — I2C bus {I2C_BUS}")
    print("=" * 44)

    bus = smbus2.SMBus(I2C_BUS)

    try:
        read_status(bus)
        display_init(bus)
        time.sleep(0.2)
        read_status(bus)

        print("\nShowing patterns — 2s each:")
        checkerboard(bus)
        time.sleep(2)

        solid_white(bus)
        time.sleep(2)

        solid_black(bus)
        time.sleep(2)

        checkerboard(bus)
        print("\nLeft on checkerboard. Ctrl+C to exit then call pattern_off() to restore.")
        input("Press ENTER to disable test pattern and return to DPI input...")

        pattern_off(bus)
        time.sleep(0.1)
        display_init(bus)
        print("Done — DPI input restored.")

    except KeyboardInterrupt:
        print("\nAborted.")
    finally:
        bus.close()


if __name__ == "__main__":
    main()
