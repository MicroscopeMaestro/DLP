#!/usr/bin/env python3
"""
DLPC3430 status reader.
Tries two read protocols: repeated-start vs separate transactions.
"""
import smbus2
import time

def find_gpio_i2c_bus():
    import os
    base = "/sys/class/i2c-dev"
    if not os.path.exists(base):
        return 5
    for entry in sorted(os.listdir(base)):
        name_file = os.path.join(base, entry, "name")
        try:
            with open(name_file) as f:
                name = f.read().strip()
            if "i2c-gpio" in name.lower() or "00000002.i2c" in name.lower():
                return int(entry.split("-")[1])
        except Exception:
            continue
    if os.path.exists("/dev/i2c-5"):
        return 5
    if os.path.exists("/dev/i2c-4"):
        return 4
    return 5

bus_num = find_gpio_i2c_bus()
bus = smbus2.SMBus(bus_num)
addr = 0x1B

def rd_repstart(reg, n):
    """Repeated-start: WRITE[cmd] + READ[n]"""
    w = smbus2.i2c_msg.write(addr, [reg])
    r = smbus2.i2c_msg.read(addr, n)
    bus.i2c_rdwr(w, r)
    return list(r)

def rd_separate(reg, n):
    """Separate transactions: WRITE[cmd] STOP START READ[n]"""
    w = smbus2.i2c_msg.write(addr, [reg])
    bus.i2c_rdwr(w)
    time.sleep(0.005)
    r = smbus2.i2c_msg.read(addr, n)
    bus.i2c_rdwr(r)
    return list(r)

REGS = [0x01, 0x02, 0x03, 0x05, 0x06, 0x07, 0x10, 0x11, 0x20, 0x21, 0x30, 0x40]

print("=== Repeated-start reads ===")
for reg in REGS:
    try:
        d = rd_repstart(reg, 4)
        print(f"  0x{reg:02X}: {[hex(x) for x in d]}")
    except Exception as e:
        print(f"  0x{reg:02X}: ERROR {e}")

print("\n=== Separate transaction reads ===")
for reg in REGS:
    try:
        d = rd_separate(reg, 4)
        print(f"  0x{reg:02X}: {[hex(x) for x in d]}")
    except Exception as e:
        print(f"  0x{reg:02X}: ERROR {e}")

bus.close()
