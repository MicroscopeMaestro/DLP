import numpy as np
import cv2
import os

try:
    from smbus2 import SMBus
except ImportError:
    SMBus = None

class DLPController:
    """
    Handles I2C communication with the DLPC3421 controller.
    """
    def __init__(self, bus_id=1, address=0x1b):
        self.bus_id = bus_id
        self.address = address
        self.bus = None
        if SMBus:
            try:
                self.bus = SMBus(bus_id)
            except Exception as e:
                print(f"Warning: Could not open I2C bus {bus_id}: {e}")
        else:
            print("Warning: smbus2 not found. I2C commands will be skipped.")

    def send_command(self, cmd, data):
        if not self.bus:
            print(f"I2C Simulator -> CMD 0x{cmd:02X}, DATA {data}")
            return
        try:
            self.bus.write_i2c_block_data(self.address, cmd, data)
        except Exception as e:
            print(f"I2C Error on CMD 0x{cmd:02X}: {e}")

    def init_dsi_mode(self):
        """
        Sends the initialization sequence to enable DSI video input.
        """
        print("Configuring DLP for DSI input mode...")
        
        # 0x05: Input Source Select (0x05 = DSI)
        self.send_command(0x05, [0x05])
        
        # 0x2E: Input Image Size (640x360)
        # Formatted as 4 bytes: [Width_LSB, Width_MSB, Height_LSB, Height_MSB]
        self.send_command(0x2E, [0x80, 0x02, 0x68, 0x01]) 
        
        # 0xD7: DSI Port Enable (0x01 = Enable)
        self.send_command(0xD7, [0x01])
        
        # 0xBD: DSI HS Clock Input (Optional, depends on your Pi's DSI clock)
        # self.send_command(0xBD, [0x00]) 

        print("Initialization commands sent.")

class PatternDisplay:
    """
    Generates and displays binary gratings in full-screen mode.
    """
    def __init__(self, width=640, height=360):
        self.width = width
        self.height = height
        self.window_name = "DLP_Output"
        
        # Create a window and force it to full screen
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def generate_grating(self, period, angle_deg):
        """
        Generates a 24-bit BGR image with a green binary grating.
        """
        x = np.arange(self.width)
        y = np.arange(self.height)
        X, Y = np.meshgrid(x, y)
        
        theta = np.radians(angle_deg)
        # Rotate coordinates
        X_rot = X * np.cos(theta) + Y * np.sin(theta)
        
        # Binary pattern
        grating = (X_rot % period < (period / 2)).astype(np.uint8) * 255
        
        # Create BGR image (Green channel only)
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img[:, :, 1] = grating
        return img

    def run(self):
        """
        Main interactive loop.
        """
        periods = [8, 16, 32, 64]
        angles = [0, 30, 60, 90, 120, 150]
        
        print("Pre-generating patterns...")
        patterns = []
        for p in periods:
            for a in angles:
                patterns.append(self.generate_grating(p, a))
        
        idx = 0
        print("\n=== DLP DSI Control ===")
        print("Keys: [N]ext Pattern, [P]revious Pattern, [Q]uit")
        
        while True:
            cv2.imshow(self.window_name, patterns[idx])
            
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('n'):
                idx = (idx + 1) % len(patterns)
                print(f"Pattern {idx+1}/{len(patterns)} (Period: {periods[idx//len(angles)]}, Angle: {angles[idx%len(angles)]})")
            elif key == ord('p'):
                idx = (idx - 1) % len(patterns)
                print(f"Pattern {idx+1}/{len(patterns)}")

        cv2.destroyAllWindows()

if __name__ == "__main__":
    # 1. Initialize Controller (I2C)
    dlp = DLPController(bus_id=1, address=0x1b)
    dlp.init_dsi_mode()
    
    # 2. Start Display (Video)
    app = PatternDisplay(640, 360)
    app.run()
