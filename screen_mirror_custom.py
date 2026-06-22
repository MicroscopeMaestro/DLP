#!/usr/bin/env python3
"""
Custom screen mirror to DLP2000 LaunchPad with color descrambling for custom wiring matrix.
"""

import argparse
import os
import struct
import sys
import time

try:
    import mss
except ImportError:
    print("Error: mss is not installed. Run: pip install mss")
    sys.exit(1)
    
try:
    import numpy as np
except ImportError:
    print("Error: numpy is not installed. Run: pip install numpy")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed. Run: pip install pillow")
    sys.exit(1)

from dlp_controller import DLPC3430

DLP_W   = 640
DLP_H   = 360

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

def descramble_colors(img_rgb: np.ndarray) -> np.ndarray:
    """
    Descramble colors from target RGB space to the permuted physical wiring space.
    """
    # Downshift to 6-bit channels
    R = (img_rgb[:, :, 0] >> 2).astype(np.uint8)
    G = (img_rgb[:, :, 1] >> 2).astype(np.uint8)
    B = (img_rgb[:, :, 2] >> 2).astype(np.uint8)

    # 1. Blue out matches Blue target (GPIO 4-9 map 1:1 to DLP LCD_DATA 0-5)
    b_out = B

    # 2. Compute r_out (RPi GPIO 16-21)
    r_out = np.zeros_like(R)
    r_out |= ((R & 0x10) >> 4)
    r_out |= ((R & 0x20) >> 4)
    r_out |= (G & 0x04)
    r_out |= (G & 0x08)
    r_out |= ((G & 0x01) << 4)
    r_out |= ((G & 0x02) << 4)

    # 3. Compute g_out (RPi GPIO 10-15)
    g_out = np.zeros_like(G)
    g_out |= ((G & 0x10) >> 4)
    g_out |= ((G & 0x20) >> 4)
    g_out |= ((R & 0x01) << 2)
    g_out |= ((R & 0x02) << 2)
    g_out |= ((R & 0x04) << 2)
    g_out |= ((R & 0x08) << 2)

    # Reconstruct 8-bit image for framebuffer writing
    out_rgb = np.zeros_like(img_rgb)
    out_rgb[:, :, 0] = r_out << 2
    out_rgb[:, :, 1] = g_out << 2
    out_rgb[:, :, 2] = b_out << 2
    
    return out_rgb

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
        print(f"Capturing: {monitor['width']}x{monitor['height']} → {DLP_W}x{DLP_H} @ {fps}fps (Descramble Active)")
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

                # Apply color descrambler for custom pinout
                frame = descramble_colors(frame)

                # Write to framebuffer
                data = frame_to_fb_bytes(frame, bpp)
                fb.seek(0)
                fb.write(data)
                fb.flush()

                elapsed = time.perf_counter() - t0
                wait    = frame_time - elapsed
                if wait > 0:
                    time.sleep(wait)

        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            fb.close()

def main():
    parser = argparse.ArgumentParser(description="Mirror RPi screen to DLP2000 via DPI with custom descramble")
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
        sys.exit(1)

    mirror_loop(fb_path, args.fps)

if __name__ == "__main__":
    main()
