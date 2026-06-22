#!/usr/bin/env python3
"""
Display a custom image fullscreen on the DLP projector (DPI-1 at 1920,0) using Pygame.
"""
import os
import sys

# Force window positioning environment variables before importing pygame
os.environ['SDL_VIDEO_WINDOW_POS'] = "1920,0"

# Set display variables for GUI session
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'
if 'WAYLAND_DISPLAY' not in os.environ:
    os.environ['WAYLAND_DISPLAY'] = 'wayland-0'

import pygame

DLP_W = 640
DLP_H = 360
DEFAULT_IMAGE = "/home/jmunozbolanos/.gemini/antigravity-cli/brain/a73666c4-40da-4c9e-99f0-f6c67a7c3a42/calibration_image_1781707521095.jpg"

def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
        
    print(f"Initializing Pygame...")
    pygame.init()
    
    # Hide mouse cursor
    pygame.mouse.set_visible(False)
    
    # Set up window (borderless, positioned at 1920,0 via environment variable)
    print("Setting up display mode...")
    screen = pygame.display.set_mode((DLP_W, DLP_H), pygame.NOFRAME)
    
    print(f"Loading and scaling image: {image_path}")
    image = pygame.image.load(image_path)
    image = pygame.transform.smoothscale(image, (DLP_W, DLP_H))
    
    # Render loop
    print("Display active. Press ESC, 'q', or close terminal to exit.")
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                    
        # Draw the image
        screen.blit(image, (0, 0))
        pygame.display.flip()
        
        # Limit frame rate to save CPU
        clock.tick(10)
        
    pygame.quit()
    print("Exited.")

if __name__ == '__main__':
    main()
