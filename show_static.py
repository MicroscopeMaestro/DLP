#!/usr/bin/env python3
"""
Display a static diagnostic test pattern on the DLP2000EVM via framebuffer.
Contains 8 vertical color bars and 4 horizontal gradients (R, G, B, W) to inspect pin integrity.
This script is self-contained so that it can run easily under sudo.
"""
import os
import sys
import numpy as np

DLP_W = 640
DLP_H = 360

def find_framebuffer() -> str:
    for fb in ["/dev/fb1", "/dev/fb0"]:
        if os.path.exists(fb):
            return fb
    raise FileNotFoundError("No framebuffer device found. Is DPI overlay enabled?")

def get_fb_info(fb_path: str) -> dict:
    name = os.path.basename(fb_path)
    base = f"/sys/class/graphics/{name}"
    bpp   = int(open(f"{base}/bits_per_pixel").read().strip())
    sizes = open(f"{base}/virtual_size").read().strip().split(",")
    return {"bpp": bpp, "width": int(sizes[0]), "height": int(sizes[1])}

def to_rgb666(frame: np.ndarray) -> np.ndarray:
    return frame & np.uint8(0xFC)

def frame_to_fb_bytes(frame: np.ndarray, bpp: int) -> bytes:
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

def generate_test_pattern() -> np.ndarray:
    # Initialize a 360x640x3 RGB frame
    frame = np.zeros((DLP_H, DLP_W, 3), dtype=np.uint8)
    
    # 1. Top 240 pixels: 8 vertical color bars
    # White, Yellow, Cyan, Green, Magenta, Red, Blue, Black
    colors = [
        [255, 255, 255], # White
        [255, 255,   0], # Yellow
        [  0, 255, 255], # Cyan
        [  0, 255,   0], # Green
        [255,   0, 255], # Magenta
        [255,   0,   0], # Red
        [  0,   0, 255], # Blue
        [  0,   0,   0]  # Black
    ]
    bar_width = DLP_W // len(colors)
    for i, color in enumerate(colors):
        frame[0:240, i*bar_width:(i+1)*bar_width] = color
        
    # 2. Bottom 120 pixels: 4 horizontal gradient bars (Red, Green, Blue, Grayscale)
    # Each bar is 30 pixels high
    for x in range(DLP_W):
        val = int((x / (DLP_W - 1)) * 255)
        # Red gradient
        frame[240:270, x] = [val, 0, 0]
        # Green gradient
        frame[270:300, x] = [0, val, 0]
        # Blue gradient
        frame[300:330, x] = [0, 0, val]
        # Grayscale gradient
        frame[330:360, x] = [val, val, val]
        
    return to_rgb666(frame)

def main():
    try:
        fb_path = find_framebuffer()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    if not os.path.exists(fb_path):
        print(f"Framebuffer {fb_path} not found.")
        sys.exit(1)
        
    fb_info = get_fb_info(fb_path)
    bpp = fb_info["bpp"]
    print(f"Writing static diagnostic pattern to {fb_path} ({bpp}bpp, {fb_info['width']}x{fb_info['height']})")
    
    pattern = generate_test_pattern()
    
    # Check if we need to resize or fit to framebuffer size
    if fb_info['width'] != DLP_W or fb_info['height'] != DLP_H:
        print(f"Warning: Framebuffer size {fb_info['width']}x{fb_info['height']} does not match DLP {DLP_W}x{DLP_H}.")
        full_frame = np.zeros((fb_info['height'], fb_info['width'], 3), dtype=np.uint8)
        h = min(DLP_H, fb_info['height'])
        w = min(DLP_W, fb_info['width'])
        full_frame[:h, :w] = pattern[:h, :w]
        data = frame_to_fb_bytes(full_frame, bpp)
    else:
        data = frame_to_fb_bytes(pattern, bpp)
        
    try:
        with open(fb_path, "wb") as fb:
            fb.write(data)
            fb.flush()
        print("Static test pattern displayed successfully on the DLP.")
    except PermissionError:
        print("Error: Permission denied. Please run this command as sudo:")
        print(f"  sudo python3 {os.path.abspath(__file__)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
