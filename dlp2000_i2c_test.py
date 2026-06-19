#!/usr/bin/env python3
"""Test I2C communication with DLP2000EVM DLPC3430 controller."""

import sys
import os

try:
    import smbus2
except ImportError:
    print("ERROR: smbus2 not found. Run: pip3 install smbus2")
    sys.exit(1)

DLPC3430_ADDR = 0x1B

def find_gpio_i2c_bus():
    """Find the i2c-gpio software bus number."""
    base = "/sys/bus/i2c/devices"
    if not os.path.exists(base):
        return None
    for entry in sorted(os.listdir(base)):
        name_file = os.path.join(base, entry, "name")
        try:
            with open(name_file) as f:
                name = f.read().strip()
            if "gpio" in name.lower() or "400000002.i2c" in name.lower():
                return int(entry.split("-")[1])
        except (IOError, ValueError, IndexError):
            continue
    # Fallback to bus 4 if it exists (standard for DLP2000 overlay configuration)
    if os.path.exists("/dev/i2c-4"):
        return 4
    return None

def read_firmware_version(bus, addr):
    """Read DLPC3430 firmware tag (command 0x05)."""
    try:
        data = bus.read_i2c_block_data(addr, 0x05, 4)
        return data
    except Exception as e:
        return None

def read_system_status(bus, addr):
    """Read system status (command 0x20)."""
    try:
        data = bus.read_i2c_block_data(addr, 0x20, 1)
        return data[0]
    except Exception as e:
        return None

def init_display(bus, addr):
    """Send display initialization commands."""
    # Source select: parallel RGB input
    bus.write_i2c_block_data(addr, 0x0c, [0x00, 0x00, 0x00, 0x1B])
    print("  Sent source select (0x0C)")
    # Display mode enable
    bus.write_i2c_block_data(addr, 0x0b, [0x00, 0x00, 0x00, 0x00])
    print("  Sent display mode (0x0B)")

def main():
    bus_num = find_gpio_i2c_bus()
    if bus_num is None:
        print("ERROR: i2c-gpio bus not found.")
        print("Fix /boot/firmware/config.txt:")
        print("  1. Change 'dtparam=i2c_arm=on' to 'dtparam=i2c_arm=off'")
        print("  2. Ensure: dtoverlay=i2c-gpio,i2c_gpio_sda=23,i2c_gpio_scl=24,i2c_gpio_delay_us=2,bus=1")
        print("  3. Reboot")
        sys.exit(1)

    print(f"i2c-gpio bus found: {bus_num}")

    try:
        bus = smbus2.SMBus(bus_num)
    except Exception as e:
        print(f"ERROR opening /dev/i2c-{bus_num}: {e}")
        print("Try: sudo python3 dlp2000_i2c_test.py")
        sys.exit(1)

    # Probe device
    try:
        bus.write_quick(DLPC3430_ADDR)
        print(f"DLPC3430 detected at 0x{DLPC3430_ADDR:02X} on bus {bus_num}")
    except Exception:
        print(f"ERROR: No device at 0x{DLPC3430_ADDR:02X} on bus {bus_num}")
        print("Check: power (5V on J3:1, 3.3V on P2:3), SDA→P2:20, SCL→P2:19, GND→P2:46")
        bus.close()
        sys.exit(1)

    # Read firmware version
    fw = read_firmware_version(bus, DLPC3430_ADDR)
    if fw:
        print(f"Firmware tag: {bytes(fw).hex()}")
    else:
        print("Firmware read failed (device may still be initializing)")

    # Read status
    status = read_system_status(bus, DLPC3430_ADDR)
    if status is not None:
        print(f"System status: 0x{status:02X}")

    # Initialize display
    print("Initializing display...")
    try:
        init_display(bus, DLPC3430_ADDR)
        print("Display initialized — projector should switch to DPI input.")
    except Exception as e:
        print(f"ERROR during init: {e}")
        bus.close()
        sys.exit(1)

    bus.close()

if __name__ == "__main__":
    main()
