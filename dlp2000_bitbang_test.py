#!/usr/bin/env python3
"""
DLP2000EVM I2C init via kernel i2c-gpio driver on /dev/i2c-4.
Requires: pip3 install smbus2
"""

import sys
import time

try:
    import smbus2
except ImportError:
    print("ERROR: smbus2 not installed. Run: pip3 install smbus2")
    sys.exit(1)

I2C_BUS = 4
DLPC3430_ADDR = 0x1B


def write_cmd(bus, addr, reg, data):
    bus.write_i2c_block_data(addr, reg, data)


def read_cmd(bus, addr, reg, length):
    write_msg = smbus2.i2c_msg.write(addr, [reg])
    read_msg = smbus2.i2c_msg.read(addr, length)
    bus.i2c_rdwr(write_msg, read_msg)
    return list(read_msg)


def scan_bus(bus):
    print(f"Scanning I2C bus {I2C_BUS}...")
    found = []
    for addr in range(0x08, 0x78):
        try:
            bus.read_byte(addr)
            found.append(addr)
            print(f"  Device found: 0x{addr:02X}")
        except OSError:
            pass
    if not found:
        print("  No devices found.")
    return found


def read_status(bus):
    addr = DLPC3430_ADDR
    try:
        data = read_cmd(bus, addr, 0x02, 1)
        print(f"  Short status (0x02): 0x{data[0]:02X}")
        print(f"    System init:  {'YES' if data[0] & 0x01 else 'NO'}")
        print(f"    Init error:   {'YES' if data[0] & 0x02 else 'NO'}")
        print(f"    DRC error:    {'YES' if data[0] & 0x04 else 'NO'}")
    except Exception as e:
        print(f"  Status read failed: {e}")

    try:
        data = read_cmd(bus, addr, 0x05, 8)
        tag = bytes(data)
        print(f"  Firmware tag (0x05): {tag.hex()} ({tag.decode('ascii', errors='replace')})")
    except Exception as e:
        print(f"  Firmware read failed: {e}")


def init_dlp(bus):
    addr = DLPC3430_ADDR
    print(f"\nInitializing DLPC3430 at 0x{addr:02X}...")

    # 0x0C: set resolution to nHD 640x360 landscape (4-byte block write)
    write_cmd(bus, addr, 0x0c, [0x00, 0x00, 0x00, 0x1B])
    print("  [1/2] Resolution nHD 640x360 (0x0C = [0x00,0x00,0x00,0x1B])")
    time.sleep(0.1)

    # 0x0B: parallel/external DPI input mode (4-byte block write)
    write_cmd(bus, addr, 0x0b, [0x00, 0x00, 0x00, 0x00])
    print("  [2/2] Parallel mode (0x0B = [0x00,0x00,0x00,0x00])")

    print("Init complete — projector should show DPI input now.")


def main():
    print(f"DLP2000EVM I2C Test (smbus2 on /dev/i2c-{I2C_BUS})")
    print("=" * 45)

    try:
        bus = smbus2.SMBus(I2C_BUS)
    except Exception as e:
        print(f"ERROR: Cannot open /dev/i2c-{I2C_BUS}: {e}")
        sys.exit(1)

    try:
        found = scan_bus(bus)

        if DLPC3430_ADDR not in found:
            print(f"\nERROR: DLPC3430 not found at 0x{DLPC3430_ADDR:02X}")
            print("Check:")
            print("  - 5V on J3:1 (Pi Pin 2)")
            print("  - 3.3V on P2:3 (Pi Pin 1)")
            print("  - GND on P2:46 (Pi Pin 6/9/14...)")
            print("  - SDA: GPIO23 (Pi Pin 16) → P2:20")
            print("  - SCL: GPIO24 (Pi Pin 18) → P2:19")
            sys.exit(1)

        read_status(bus)
        init_dlp(bus)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
