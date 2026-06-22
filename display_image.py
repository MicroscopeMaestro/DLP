#!/usr/bin/env python3
"""
Display a custom image fullscreen on the DLP projector (DPI-1 at 1920,0).
Uses OpenCV window rendering to bypass Wayland's framebuffer lock.
"""
import os
import sys
import cv2
import numpy as np

DLP_W = 640
DLP_H = 360
DEFAULT_IMAGE = "/home/jmunozbolanos/.gemini/antigravity-cli/brain/a73666c4-40da-4c9e-99f0-f6c67a7c3a42/calibration_image_1781707521095.jpg"

def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
        
    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not decode image.")
        sys.exit(1)
        
    # Resize to projector native resolution (640x360)
    print(f"Resizing image to {DLP_W}x{DLP_H}...")
    resized_img = cv2.resize(img, (DLP_W, DLP_H), interpolation=cv2.INTER_LANCZOS4)
    
    # DLPC2607 uses RGB666, quantize to clear lower 2 bits (OpenCV is BGR)
    resized_img = resized_img & 0xFC
    
    # Configure environmental variables to force X11 backend under Wayland
    os.environ["GDK_BACKEND"] = "x11"
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    window_name = "DLP_Projector_Image"
    
    print("Opening display window...")
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Move window to extended display coordinates (DPI-1 at 1920,0)
    print("Positioning window at 1920,0...")
    cv2.moveWindow(window_name, 1920, 0)
    
    # Make window fullscreen
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # Display the image
    cv2.imshow(window_name, resized_img)
    
    print("Image displayed. Press 'q' or Esc in the window or Ctrl+C in terminal to exit.")
    
    while True:
        key = cv2.waitKey(100) & 0xFF
        if key == ord('q') or key == 27: # 'q' or ESC
            break
            
    cv2.destroyAllWindows()
    print("Exiting display.")

if __name__ == '__main__':
    main()
