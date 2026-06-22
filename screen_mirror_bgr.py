#!/usr/bin/env python3
"""
Screen mirror to DLP2000 EVM with standard RGB to BGR channel swap correction.
Corrects physical Red-Blue channel swap in software.
"""
import argparse
import os
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
    for fb in ["/dev/fb0", "/dev/fb1"]:
        if os.path.exists(fb):
            return fb
    raise FileNotFoundError("No framebuffer device found.")

def get_fb_info(fb_path: str) -> dict:
    name = os.path.basename(fb_path)
    base = f"/sys/class/graphics/{name}"
    bpp   = int(open(f"{base}/bits_per_pixel").read().strip())
    sizes = open(f"{base}/virtual_size").read().strip().split(",")
    return {"bpp": bpp, "width": int(sizes[0]), "height": int(sizes[1])}

def swap_rb_channels(img_rgb: np.ndarray) -> np.ndarray:
    """Swap Red and Blue channels: RGB -> BGR."""
    return img_rgb[:, :, [2, 1, 0]]

def frame_to_fb_bytes(frame: np.ndarray, bpp: int) -> bytes:
    if bpp == 32:
        # XRGB8888: [B, G, R, A/X]
        alpha = np.zeros((*frame.shape[:2], 1), dtype=np.uint8)
        bgra  = np.concatenate([frame[:, :, ::-1], alpha], axis=2)  # BGR -> RGB + alpha
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
        monitor = sct.monitors[1]
        print(f"Capturing: {monitor['width']}x{monitor['height']} → {DLP_W}x{DLP_H} @ {fps}fps (R-B Swap Active)")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                t0 = time.perf_counter()

                # Capture screen
                raw = sct.grab(monitor)
                img = Image.frombytes("RGB", (raw.width, raw.height), raw.rgb)

                # Resize to projector native
                img = img.resize((DLP_W, DLP_H), Image.Resampling.BILINEAR)
                frame = np.array(img, dtype=np.uint8)

                # Swap Red and Blue
                frame = swap_rb_channels(frame)

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
    parser = argparse.ArgumentParser(description="Mirror RPi screen to DLP2000 with R-B channel swap")
    parser.add_argument("--fps",     type=int,  default=15,    help="Target frames per second")
    parser.add_argument("--fb",      type=str,  default=None,  help="Framebuffer device")
    args = parser.parse_args()

    # Find and open framebuffer
    fb_path = args.fb or find_framebuffer()
    if not os.path.exists(fb_path):
        print(f"ERROR: Framebuffer {fb_path} not found.")
        sys.exit(1)

    mirror_loop(fb_path, args.fps)

if __name__ == "__main__":
    main()
