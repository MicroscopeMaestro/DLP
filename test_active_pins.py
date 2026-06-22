#!/usr/bin/env python3
import os
import sys
import time
import subprocess

# Force window positioning to 0,0
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
os.environ['DISPLAY'] = ':0'
os.environ['WAYLAND_DISPLAY'] = 'wayland-0'

try:
    import pygame
except ImportError:
    print("Error: pygame not installed.")
    sys.exit(1)

def read_gpios(label):
    print(f"\n--- GPIO States during {label} ---")
    result = subprocess.run("pinctrl get 4-9,16-21", shell=True, text=True, capture_output=True)
    lines = result.stdout.strip().split('\n')
    
    blue_high = []
    red_high = []
    
    for line in lines:
        if "//" in line:
            parts = line.split("//")
            pin_info = parts[0].strip()
            comment = parts[1].strip()
            
            pin_num = int(pin_info.split(":")[0])
            is_high = "hi" in pin_info
            
            if pin_num in range(4, 10):
                if is_high:
                    blue_high.append(f"GPIO {pin_num} ({comment.split('=')[1]})")
            elif pin_num in range(16, 22):
                if is_high:
                    red_high.append(f"GPIO {pin_num} ({comment.split('=')[1]})")
                    
    print("  Active Blue Pins (GPIO 4-9):", blue_high if blue_high else "NONE")
    print("  Active Red Pins (GPIO 16-21):", red_high if red_high else "NONE")

def main():
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((640, 360), pygame.FULLSCREEN | pygame.NOFRAME)
    
    clock = pygame.time.Clock()
    running = True
    step = 0
    start_time = time.time()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                    
        elapsed = time.time() - start_time
        
        if step == 0 and elapsed >= 1.0:
            # Solid Red Screen
            screen.fill((252, 0, 0))
            pygame.display.flip()
            step = 1
            
        elif step == 1 and elapsed >= 1.5:
            read_gpios("Solid Red Screen")
            step = 2
            
        elif step == 2 and elapsed >= 3.0:
            # Solid Blue Screen
            screen.fill((0, 0, 252))
            pygame.display.flip()
            step = 3
            
        elif step == 3 and elapsed >= 3.5:
            read_gpios("Solid Blue Screen")
            step = 4
            
        elif step == 4 and elapsed >= 5.0:
            running = False
            
        clock.tick(30)
        
    pygame.quit()
    print("\nTest completed.")

if __name__ == "__main__":
    main()
