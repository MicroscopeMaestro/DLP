"""
Display a random image on DLP2000 via framebuffer.
Usage:
  python3 show_random.py             # one random frame, hold until Ctrl+C
  python3 show_random.py --animate   # new random frame every second
  python3 show_random.py --fb /dev/fb0
"""

import argparse
import os
import sys
import time

import numpy as np

from dlp_controller import DLPC3430
from screen_mirror import find_framebuffer, get_fb_info, frame_to_fb_bytes, to_rgb666

DLP_W = 640
DLP_H = 360


def random_frame() -> np.ndarray:
    return to_rgb666(np.random.randint(0, 256, (DLP_H, DLP_W, 3), dtype=np.uint8))


def write_frame(fb, frame: np.ndarray, bpp: int):
    data = frame_to_fb_bytes(frame, bpp)
    fb.seek(0)
    fb.write(data)
    fb.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fb",      default=None)
    parser.add_argument("--animate", action="store_true", help="Cycle random frames at 1fps")
    parser.add_argument("--no-init", action="store_true")
    args = parser.parse_args()

    if not args.no_init:
        try:
            dlp = DLPC3430()
            dlp.init_external_video(DLP_W, DLP_H)
            dlp.set_leds(r=True, g=True, b=True, current=200)
            dlp.close()
            print("DLPC3430 configured.")
        except Exception as e:
            print(f"I2C init failed: {e}  (continuing anyway)")

    fb_path = args.fb or find_framebuffer()
    if not os.path.exists(fb_path):
        print(f"Framebuffer {fb_path} not found. Enable DPI overlay and reboot.")
        sys.exit(1)

    fb_info = get_fb_info(fb_path)
    bpp = fb_info["bpp"]
    print(f"Writing to {fb_path} ({bpp}bpp)")

    with open(fb_path, "wb") as fb:
        if args.animate:
            print("Animating random frames. Ctrl+C to stop.")
            try:
                while True:
                    write_frame(fb, random_frame(), bpp)
                    time.sleep(1.0)
            except KeyboardInterrupt:
                print("\nStopped.")
        else:
            frame = random_frame()
            write_frame(fb, frame, bpp)
            print("Random image displayed. Press Ctrl+C to clear.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                # Clear to black on exit
                write_frame(fb, np.zeros((DLP_H, DLP_W, 3), dtype=np.uint8), bpp)
                print("\nCleared.")


if __name__ == "__main__":
    main()
