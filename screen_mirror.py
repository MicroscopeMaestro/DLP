"""
Screen mirror to DLP2000 LaunchPad via Raspberry Pi DPI (RGB666 parallel video).

Hardware setup:
  - RPi GPIO → DLP2000 LaunchPad 40-pin parallel video header
  - RPi /boot/config.txt must have DPI overlay enabled (see below)
  - I2C (GPIO2/3) → DLPC3430 for control

Required /boot/config.txt entries:
  dtoverlay=dpi18
  enable_dpi_lcd=1
  display_default_lcd=0          # keep HDMI as primary
  dpi_group=2
  dpi_mode=87
  dpi_output_format=0x6f005      # RGB666, DE mode, active-high syncs
  hdmi_timings=640 0 10 10 20 360 0 5 5 10 0 0 0 60 0 32000000 1

After rebooting, DLP should appear as /dev/fb1 (framebuffer 1).

Usage:
  python3 screen_mirror.py                # mirror display :0
  python3 screen_mirror.py --fps 15       # set target frame rate
  python3 screen_mirror.py --no-init      # skip I2C init (DLP already configured)
  python3 screen_mirror.py --fb /dev/fb0  # override framebuffer device
"""

import argparse
import os
import struct
import sys
import time

import mss
import numpy as np
from PIL import Image

from dlp_controller import DLPC3430

DLP_W   = 640
DLP_H   = 360
FB_DEV  = "/dev/fb1"


def find_framebuffer() -> str:
    """Return the DPI framebuffer path, or raise if not found."""
    for fb in ["/dev/fb1", "/dev/fb0"]:
        if os.path.exists(fb):
            return fb
    raise FileNotFoundError("No framebuffer device found. Is DPI overlay enabled?")


def get_fb_info(fb_path: str) -> dict:
    """Read framebuffer pixel format from sysfs."""
    name = os.path.basename(fb_path)
    base = f"/sys/class/graphics/{name}"
    bpp   = int(open(f"{base}/bits_per_pixel").read().strip())
    sizes = open(f"{base}/virtual_size").read().strip().split(",")
    return {"bpp": bpp, "width": int(sizes[0]), "height": int(sizes[1])}


def to_rgb666(frame: np.ndarray) -> np.ndarray:
    """Quantize RGB888 array to RGB666 (zeroes bottom 2 bits per channel)."""
    return frame & np.uint8(0xFC)


def frame_to_fb_bytes(frame: np.ndarray, bpp: int) -> bytes:
    """Convert HxWx3 uint8 RGB frame to raw framebuffer bytes."""
    if bpp == 32:
        # XRGB8888: pad each pixel with a zero byte
        alpha = np.zeros((*frame.shape[:2], 1), dtype=np.uint8)
        bgra  = np.concatenate([frame[:, :, ::-1], alpha], axis=2)  # RGB→BGR + alpha
        return bgra.tobytes()
    elif bpp == 16:
        # RGB565
        r = (frame[:, :, 0] >> 3).astype(np.uint16)
        g = (frame[:, :, 1] >> 2).astype(np.uint16)
        b = (frame[:, :, 2] >> 3).astype(np.uint16)
        rgb565 = ((r << 11) | (g << 5) | b).astype(np.uint16)
        return rgb565.tobytes()
    else:
        raise ValueError(f"Unsupported framebuffer bpp: {bpp}")


def mirror_loop(fb_path: str, fps: int):
    fb_info = get_fb_info(fb_path)
    bpp     = fb_info["bpp"]
    print(f"Framebuffer: {fb_path}  {fb_info['width']}x{fb_info['height']} @ {bpp}bpp")

    frame_time = 1.0 / fps
    fb         = open(fb_path, "wb")

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # monitor[0] = all monitors, [1] = primary
        print(f"Capturing: {monitor['width']}x{monitor['height']} → {DLP_W}x{DLP_H} @ {fps}fps")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                t0 = time.perf_counter()

                # Capture primary display
                raw = sct.grab(monitor)
                img = Image.frombytes("RGB", (raw.width, raw.height), raw.rgb)

                # Scale to DLP native resolution
                img = img.resize((DLP_W, DLP_H), Image.Resampling.LANCZOS)
                frame = np.array(img, dtype=np.uint8)

                # Reduce to RGB666 color depth
                frame = to_rgb666(frame)

                # Write to framebuffer
                data = frame_to_fb_bytes(frame, bpp)
                fb.seek(0)
                fb.write(data)
                fb.flush()

                elapsed = time.perf_counter() - t0
                wait    = frame_time - elapsed
                if wait > 0:
                    time.sleep(wait)
                else:
                    # Running behind — skip sleep, log every 30 frames
                    pass

        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            fb.close()


def main():
    parser = argparse.ArgumentParser(description="Mirror RPi screen to DLP2000 via DPI RGB666")
    parser.add_argument("--fps",     type=int,  default=10,    help="Target frames per second")
    parser.add_argument("--fb",      type=str,  default=None,  help="Framebuffer device (default: auto)")
    parser.add_argument("--no-init", action="store_true",      help="Skip DLPC3430 I2C initialization")
    args = parser.parse_args()

    # Configure DLP via I2C
    if not args.no_init:
        try:
            print("Initializing DLPC3430 via I2C...")
            dlp = DLPC3430()
            status = dlp.read_status()
            print(f"  Status: {status}")
            dlp.init_external_video(DLP_W, DLP_H)
            dlp.set_leds(r=True, g=True, b=True, current=200)
            dlp.close()
            print("  DLPC3430 configured for external RGB666 video.\n")
        except Exception as e:
            print(f"  I2C init failed: {e}")
            print("  Continuing without I2C config (use --no-init to suppress this warning).\n")

    # Find and open framebuffer
    fb_path = args.fb or find_framebuffer()
    if not os.path.exists(fb_path):
        print(f"ERROR: Framebuffer {fb_path} not found.")
        print("Check that dtoverlay=dpi18 is in /boot/config.txt and RPi has rebooted.")
        sys.exit(1)

    mirror_loop(fb_path, args.fps)


if __name__ == "__main__":
    main()
