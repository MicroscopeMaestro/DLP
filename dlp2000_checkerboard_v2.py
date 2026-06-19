#!/usr/bin/env python3
"""
Checkerboard via I2C only — no mode-switching init commands.
Run AFTER power cycling DLP2000EVM (device must show default image first).
"""
import smbus2, time
from smbus2 import i2c_msg

bus = smbus2.SMBus(4)
ADDR = 0x1B

def wr(cmd, data):
    bus.write_i2c_block_data(ADDR, cmd, data)

def rd(cmd, n):
    try:
        w = i2c_msg.write(ADDR, [cmd])
        r = i2c_msg.read(ADDR, n)
        bus.i2c_rdwr(w, r)
        return list(r)
    except Exception as e:
        return [0]

print("ShortStatus:", rd(0x02, 1))

print("Sending checkerboard (0x1A)...")
wr(0x1A, [0x01, 0x04, 0x02, 0x00])
time.sleep(3)
print("  -> see checkerboard?")

print("Solid white (0x1A)...")
wr(0x1A, [0x01, 0x00, 0x02, 0xFF])
time.sleep(3)
print("  -> see white?")

print("Solid black (0x1A)...")
wr(0x1A, [0x01, 0x01, 0x02, 0x00])
time.sleep(3)
print("  -> see black?")

print("Back to checkerboard...")
wr(0x1A, [0x01, 0x04, 0x02, 0x00])
print("Held on checkerboard. Ctrl+C to exit.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

bus.close()
