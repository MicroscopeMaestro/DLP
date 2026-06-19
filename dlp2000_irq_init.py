#!/usr/bin/env python3
"""
DLPC3430 HOST_IRQ handshake + checkerboard.
Wire: DLP2000EVM P2:21 -> RPi GPIO25 (header pin 22).
"""
import lgpio, smbus2, time
from smbus2 import i2c_msg

I2C_BUS = 4
DLPC_ADDR = 0x1B
IRQ_GPIO = 25

def wr(bus, cmd, data):
    bus.write_i2c_block_data(DLPC_ADDR, cmd, data)

def rd(bus, cmd, n):
    w = i2c_msg.write(DLPC_ADDR, [cmd])
    r = i2c_msg.read(DLPC_ADDR, n)
    bus.i2c_rdwr(w, r)
    return list(r)

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, IRQ_GPIO, lgpio.SET_PULL_UP)

bus = smbus2.SMBus(I2C_BUS)

print("Monitoring HOST_IRQ on GPIO25 for 30s...")
print("(Power cycle DLP2000EVM now if not already done)")
print()

deadline = time.time() + 30
irq_seen = False

while time.time() < deadline:
    irq = lgpio.gpio_read(h, IRQ_GPIO)
    status_raw = rd(bus, 0x02, 1)[0]
    elapsed = 30 - (deadline - time.time())
    print(f"[{elapsed:4.1f}s] HOST_IRQ={irq} ShortStatus=0x{status_raw:02X}", end='\r')

    if irq == 0:  # IRQ asserted (active low)
        print(f"\n*** HOST_IRQ LOW at {elapsed:.1f}s — ACKing...")
        irq_seen = True
        # ACK by reading status
        st = rd(bus, 0x02, 1)
        fw = rd(bus, 0x05, 8)
        print(f"  ShortStatus: {[hex(x) for x in st]}")
        print(f"  FirmwareTag: {bytes(fw)}")
        break

    time.sleep(0.2)

if not irq_seen:
    print(f"\nNo HOST_IRQ seen. ShortStatus still: 0x{rd(bus, 0x02, 1)[0]:02X}")
    print("Check: is P2:21 connected to GPIO25?")
else:
    print("\nSending checkerboard pattern...")
    wr(bus, 0x1A, [0x01, 0x04, 0x02, 0x00])
    time.sleep(0.5)
    wr(bus, 0x1A, [0x01, 0x07, 0x02, 0x00])  # try pattern 7 too
    print("Done.")

bus.close()
lgpio.gpiochip_close(h)
