#!/usr/bin/env python3
"""
Display a static diagnostic test pattern in a fullscreen window on the DLP projector (DPI-1 at 1920,0).
This avoids the window manager overwriting raw framebuffer writes under Wayland.
"""
import os
import sys
import numpy as np
import cv2

DLP_W = 640
DLP_H = 360

def generate_test_pattern() -> np.ndarray:
    # Initialize a 360x640x3 RGB frame (OpenCV uses BGR, so we construct BGR directly)
    # BGR colors: [B, G, R]
    colors = [
        [255, 255, 255], # White
        [  0, 255, 255], # Yellow (R=255, G=255)
        [255, 255,   0], # Cyan (G=255, B=255)
        [  0, 255,   0], # Green (G=255)
        [255,   0, 255], # Magenta (R=255, B=255)
        [  0,   0, 255], # Red (R=255)
        [255,   0,   0], # Blue (B=255)
        [  0,   0,   0]  # Black
    ]
    
    frame = np.zeros((DLP_H, DLP_W, 3), dtype=np.uint8)
    
    # 1. Top 240 pixels: 8 vertical color bars
    bar_width = DLP_W // len(colors)
    for i, color in enumerate(colors):
        frame[0:240, i*bar_width:(i+1)*bar_width] = color
        
    # 2. Bottom 120 pixels: 4 horizontal gradient bars (Red, Green, Blue, Grayscale)
    # Each bar is 30 pixels high
    for x in range(DLP_W):
        val = int((x / (DLP_W - 1)) * 255)
        # Red gradient [0, 0, val]
        frame[240:270, x] = [0, 0, val]
        # Green gradient [0, val, 0]
        frame[270:300, x] = [0, val, 0]
        # Blue gradient [val, 0, 0]
        frame[300:330, x] = [val, 0, 0]
        # Grayscale gradient [val, val, val]
        frame[330:360, x] = [val, val, val]
        
    # DLP2000 uses RGB666, so clear lower 2 bits of each channel for hardware alignment
    frame = frame & 0xFC
    return frame

def main():
    # Force X11 backend if running under Wayland, to allow absolute window positioning
    os.environ["GDK_BACKEND"] = "x11"
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    pattern = generate_test_pattern()
    window_name = "DLP_Diagnostic_Pattern"
    
    print("Creating window...")
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Move window to the coordinate of DPI-1 (x=1920, y=0)
    print("Moving window to DPI-1 coordinates (1920, 0)...")
    cv2.moveWindow(window_name, 1920, 0)
    
    # Set to fullscreen
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # Show the pattern
    cv2.imshow(window_name, pattern)
    
    print("Pattern displayed. Press 'q' or Ctrl+C in terminal to exit.")
    
    while True:
        key = cv2.waitKey(100) & 0xFF
        if key == ord('q') or key == 27: # 'q' or ESC
            break
            
    cv2.destroyAllWindows()
    print("Exiting.")

if __name__ == '__main__':
    main()
