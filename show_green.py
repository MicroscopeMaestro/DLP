#!/usr/bin/env python3
"""
Display a solid Green screen on the projector to verify the Green channel.
"""
import os
import sys

os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
os.environ['DISPLAY'] = ':0'
os.environ['WAYLAND_DISPLAY'] = 'wayland-0'

try:
    import pygame
except ImportError:
    print("Error: pygame is not installed.")
    sys.exit(1)

def main():
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((640, 360), pygame.FULLSCREEN | pygame.NOFRAME)
    
    # Fill with solid Green (252 matches RGB666 alignment)
    screen.fill((0, 252, 0))
    pygame.display.flip()
    
    print("Solid Green screen active. Press ESC or 'q' to exit.")
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
