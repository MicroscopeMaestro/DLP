#!/usr/bin/env python3
"""
Display a solid white screen on the projector to test isolated color channels.
"""
import os
import sys

# Force window positioning to projector screen (0,0)
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'
if 'WAYLAND_DISPLAY' not in os.environ:
    os.environ['WAYLAND_DISPLAY'] = 'wayland-0'

try:
    import pygame
except ImportError:
    print("Error: pygame is not installed.")
    sys.exit(1)

def main():
    print("Initializing Pygame...")
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((640, 360), pygame.NOFRAME)
    
    # Draw solid white (252 is 63 shifted left by 2 bits, matching RGB666 alignment)
    screen.fill((252, 252, 252))
    pygame.display.flip()
    
    print("Solid white signal active. Press ESC or 'q' to exit.")
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
        clock.tick(10)
        
    pygame.quit()

if __name__ == '__main__':
    main()
