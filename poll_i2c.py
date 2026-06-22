#!/usr/bin/env python3
import time
import subprocess
from smbus2 import SMBus

def set_pullups():
    try:
        subprocess.run(["pinctrl", "set", "23,24", "pu"], check=True)
        print("Set internal pull-ups on GPIO 23/24.")
    except Exception as e:
        print(f"Warning: Could not set GPIO pull-ups via pinctrl: {e}")

def main():
    print("Starting real-time I2C monitor for DLP2000 (address 0x1b)...")
    set_pullups()
    
    bus_id = 1
    addr = 0x1b
    
    last_state = None
    
    try:
        while True:
            try:
                # Open SMBus dynamically to reset state on each probe
                with SMBus(bus_id) as bus:
                    # Read input source configuration (register 0x05)
                    # If this succeeds, the projector is communicating!
                    val = bus.read_i2c_block_data(addr, 0x05, 1)
                    
                    if last_state != "connected":
                        print("\n[SUCCESS] Projector detected at 0x1b!")
                        print("Initializing parallel video mode (640x360)...")
                        
                        # Set resolution: nHD 640x360 landscape (0x1B)
                        bus.write_i2c_block_data(addr, 0x0c, [0x00, 0x00, 0x00, 0x1b])
                        time.sleep(0.05)
                        
                        # Select parallel RGB input (0x00)
                        bus.write_i2c_block_data(addr, 0x0b, [0x00, 0x00, 0x00, 0x00])
                        time.sleep(0.05)
                        
                        # Enable LEDs
                        bus.write_i2c_block_data(addr, 0x16, [0x00, 0x00, 0x00, 0x07])
                        
                        print("Initialization completed successfully. It should now show your mirrored screen!")
                        last_state = "connected"
                        break
            except OSError:
                if last_state != "disconnected":
                    print("Projector not found (I2C NACK). Still showing splash screen...")
                    print("--> Check that VINTF (P2 Pin 3) is connected to 3.3V on RPi.")
                    print("--> Try swapping SDA (P2 Pin 20) and SCL (P2 Pin 19) wires.")
                    last_state = "disconnected"
            
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nExited monitor.")

if __name__ == "__main__":
    main()
