"""
DLPC3430 I2C controller for DLP2000 LaunchPad (DLPDLCR2000EVM).
Controls via smbus2 over Raspberry Pi GPIO I2C (bus 1, pins SDA=GPIO2 SCL=GPIO3).
Reference: DLPC3430 Programmer's Guide DLPU077.
"""

import time
from smbus2 import SMBus, i2c_msg

DLPC3430_ADDR = 0x1B  # 7-bit I2C address

# DLPC3430 write command IDs (DLPU077)
CMD_SHORT_STATUS          = 0xD0  # Read: 1 byte status
CMD_INPUT_SOURCE          = 0x05  # Write: select video input
CMD_INPUT_IMAGE_SIZE      = 0x2E  # Write: [W_LSB W_MSB H_LSB H_MSB]
CMD_LED_ENABLE            = 0x52  # Write: [R_en G_en B_en]  (1=on 0=off)
CMD_LED_CURRENT           = 0x54  # Write: [R G B]  each 0-255 maps to 0-1023mA
CMD_OPERATING_MODE        = 0x04  # Write: operating mode select

# CMD_INPUT_SOURCE values
INPUT_EXTERNAL_VIDEO      = 0x00  # Parallel RGB from GPIO header
INPUT_TEST_PATTERN        = 0x02  # Internal test pattern generator
INPUT_SPLASH_SCREEN       = 0x04  # Splash image stored in flash
INPUT_DSI                 = 0x05  # MIPI DSI (not used for parallel RGB)

# CMD_OPERATING_MODE values
OPMODE_DISPLAY_VIDEO      = 0x00  # Display external/splash/test video
OPMODE_PATTERN_SEQUENCE   = 0x04  # Pattern sequence mode (not used here)


def find_dlp_i2c_bus() -> int:
    import glob
    for path in glob.glob("/sys/bus/i2c/devices/i2c-*/of_node/compatible"):
        try:
            with open(path, "r") as f:
                if "i2c-gpio" in f.read():
                    bus_name = path.split("/")[-3]
                    return int(bus_name.replace("i2c-", ""))
        except Exception:
            pass
    return 1


class DLPC3430:
    def __init__(self, bus_id=None, address=DLPC3430_ADDR):
        if bus_id is None:
            bus_id = find_dlp_i2c_bus()
        self.bus = SMBus(bus_id)
        self.addr = address

    def write_cmd(self, cmd, data: list):
        self.bus.write_i2c_block_data(self.addr, cmd, data)

    def read_cmd(self, cmd, length: int) -> list:
        write = i2c_msg.write(self.addr, [cmd])
        read  = i2c_msg.read(self.addr, length)
        self.bus.i2c_rdwr(write, read)
        return list(read)

    def read_status(self) -> dict:
        raw = self.read_cmd(CMD_SHORT_STATUS, 1)[0]
        return {
            "system_initialized": bool(raw & 0x01),
            "init_error":         bool(raw & 0x02),
            "dmd_error":          bool(raw & 0x08),
            "app_running":        bool(raw & 0x20),
        }

    def wait_for_init(self, timeout=15.0) -> bool:
        """Poll until system_initialized=True or timeout. Returns True on success."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                s = self.read_status()
                if s["system_initialized"]:
                    return True
            except Exception:
                pass
            time.sleep(0.25)
        return False

    def init_external_video(self, width=640, height=360):
        """Configure DLPC3430 to accept parallel RGB video from GPIO header."""
        # External parallel video input (RGB666 from RPi DPI)
        self.write_cmd(CMD_INPUT_SOURCE, [INPUT_EXTERNAL_VIDEO])
        time.sleep(0.05)

        # Set expected input resolution
        self.write_cmd(CMD_INPUT_IMAGE_SIZE, [
            width  & 0xFF, (width  >> 8) & 0xFF,
            height & 0xFF, (height >> 8) & 0xFF,
        ])
        time.sleep(0.05)

        # Set operating mode to display video
        self.write_cmd(CMD_OPERATING_MODE, [OPMODE_DISPLAY_VIDEO])
        time.sleep(0.1)

    def set_leds(self, r=True, g=True, b=True, current=200):
        """Enable RGB LEDs. current: 0-255, scales LED drive strength."""
        self.write_cmd(CMD_LED_ENABLE,  [int(r), int(g), int(b)])
        self.write_cmd(CMD_LED_CURRENT, [current, current, current])

    def close(self):
        self.bus.close()


def main():
    print("Connecting to DLPC3430...")
    dlp = DLPC3430()

    status = dlp.read_status()
    print(f"Status: {status}")

    if not status["system_initialized"]:
        print("Waiting for DLPC3430 to initialize (up to 15s)...")
        if not dlp.wait_for_init(timeout=15.0):
            print("WARNING: DLPC3430 did not initialize — check power and I2C wiring.")
        else:
            print(f"Initialized. Status: {dlp.read_status()}")

    print("Configuring external video mode (RGB666, 640x360)...")
    dlp.init_external_video(640, 360)

    print("Enabling LEDs...")
    dlp.set_leds(r=True, g=True, b=True, current=200)

    print("Done. DLP ready for video input.")
    dlp.close()


if __name__ == "__main__":
    main()
