#!/usr/bin/env python3
import time
import sys
import os

def main():
    fb_path = "/dev/fb0"
    if not os.path.exists(fb_path):
        print(f"Error: {fb_path} does not exist.")
        sys.exit(1)
        
    # XRGB8888 format: 4 bytes per pixel [B, G, R, A/X]
    # We want Red = 240, Green = 12, Blue = 0
    # Bytes: B=0, G=12, R=240, A=0 -> b'\x00\x0c\xf0\x00'
    pixel = b'\x00\x0c\xf0\x00'
    
    # 640x360 pixels
    num_pixels = 640 * 360
    frame_data = pixel * num_pixels
    
    print(f"Writing direct XRGB8888 (240, 12, 0) to {fb_path} in a loop. Press Ctrl+C to stop...")
    
    try:
        fd = os.open(fb_path, os.O_RDWR)
        while True:
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, frame_data)
            time.sleep(0.01) # Write 100 times per second to override compositor
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            os.close(fd)
        except:
            pass

if __name__ == "__main__":
    main()
