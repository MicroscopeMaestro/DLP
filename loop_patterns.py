#!/usr/bin/env python3
"""
Loop through a series of diagnostic and structural patterns on the DLP2000 projector.
Supports both:
  1. Software-rendered custom patterns (rendered full-screen via Pygame)
  2. Hardware-rendered internal test patterns (configured via I2C commands)
"""

import sys
import os
import time
import argparse
import subprocess
import glob
import numpy as np

# Ensure Pygame is available
try:
    import pygame
except ImportError:
    print("Error: pygame is not installed. Please run: pip install pygame")
    sys.exit(1)

DLP_W = 640
DLP_H = 360

# --- Helper to find software I2C bus ---
def find_dlp_i2c_bus() -> int:
    for path in glob.glob("/sys/bus/i2c/devices/i2c-*/of_node/compatible"):
        try:
            with open(path, "r") as f:
                if "i2c-gpio" in f.read():
                    bus_name = path.split("/")[-3]
                    return int(bus_name.replace("i2c-", ""))
        except Exception:
            pass
    return 5

# --- hardware I2C control ---
def set_dlp_source(bus_num, source_val):
    # Register 0x0b controls input source
    subprocess.run(["i2cset", "-y", str(bus_num), "0x1b", "0x0b", "0x00", "0x00", "0x00", f"0x{source_val:02X}", "i"], check=True)

def set_dlp_pattern(bus_num, pattern_idx):
    # Register 0x11 controls test pattern selection
    pattern_bytes = ["0x00", "0x00", "0x00", f"0x{pattern_idx:02X}"]
    subprocess.run(["i2cset", "-y", str(bus_num), "0x1b", "0x11"] + pattern_bytes + ["i"], check=True)


# --- Pattern Generators for Pygame ---
def make_solid_color(color):
    surf = pygame.Surface((DLP_W, DLP_H))
    surf.fill(color)
    return surf

def make_checkerboard(square_size=40):
    surf = pygame.Surface((DLP_W, DLP_H))
    surf.fill((255, 255, 255))
    for y in range(0, DLP_H, square_size * 2):
        for x in range(0, DLP_W, square_size * 2):
            pygame.draw.rect(surf, (0, 0, 0), (x, y, square_size, square_size))
            pygame.draw.rect(surf, (0, 0, 0), (x + square_size, y + square_size, square_size, square_size))
    return surf

def make_stripes(vertical=True, stripe_width=10):
    surf = pygame.Surface((DLP_W, DLP_H))
    surf.fill((255, 255, 255))
    if vertical:
        for x in range(0, DLP_W, stripe_width * 2):
            pygame.draw.rect(surf, (0, 0, 0), (x, 0, stripe_width, DLP_H))
    else:
        for y in range(0, DLP_H, stripe_width * 2):
            pygame.draw.rect(surf, (0, 0, 0), (0, y, DLP_W, stripe_width))
    return surf

def make_grayscale_ramp():
    surf = pygame.Surface((DLP_W, DLP_H))
    for x in range(DLP_W):
        val = int((x / (DLP_W - 1)) * 255)
        # Apply RGB666 alignment (zero out bottom 2 bits)
        val = val & 0xFC
        pygame.draw.line(surf, (val, val, val), (x, 0), (x, DLP_H))
    return surf


# --- Main Loop functions ---
def run_software_loop(interval):
    print("Initializing Pygame window...")
    # Position window at 0,0 since DPI-1 is at +0+0 in single screen setup
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((DLP_W, DLP_H), pygame.FULLSCREEN | pygame.NOFRAME)
    
    # Define our suite of patterns
    patterns = [
        ("Solid Red", make_solid_color((252, 0, 0))),   # Aligned to RGB666
        ("Solid Green", make_solid_color((0, 252, 0))),
        ("Solid Blue", make_solid_color((0, 0, 252))),
        ("Checkerboard", make_checkerboard(40)),
        ("Fine Checkerboard", make_checkerboard(10)),
        ("Vertical Stripes", make_stripes(vertical=True, stripe_width=20)),
        ("Fine Vertical Stripes", make_stripes(vertical=True, stripe_width=2)),
        ("Horizontal Stripes", make_stripes(vertical=False, stripe_width=20)),
        ("Grayscale Ramp", make_grayscale_ramp())
    ]
    
    print(f"Loaded {len(patterns)} custom patterns. Starting loop (interval: {interval}s).")
    print("Press ESC or Ctrl+C to exit.")
    
    idx = 0
    last_switch = 0
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
        
        now = time.time()
        if now - last_switch >= interval:
            name, surf = patterns[idx]
            print(f"Displaying: {name}")
            screen.blit(surf, (0, 0))
            pygame.display.flip()
            idx = (idx + 1) % len(patterns)
            last_switch = now
            
        time.sleep(0.05)
        
    pygame.quit()
    print("Software pattern loop finished.")


def run_hardware_loop(interval):
    bus_num = find_dlp_i2c_bus()
    print(f"Setting DLP2000 input source to Internal Test Pattern (bus {bus_num})...")
    set_dlp_source(bus_num, 1)
    
    # Standard hardware patterns on the DLPC2607
    hardware_patterns = [
        ("Checkerboard", 0),
        ("Solid Color (White/Black)", 1),
        ("Vertical Gray Ramp", 2),
        ("Horizontal Gray Ramp", 3),
        ("Grid / Crosshatch", 4),
        ("Diagonal Lines", 5),
        ("Vertical Lines", 6),
        ("Horizontal Lines", 7),
    ]
    
    print(f"Looping {len(hardware_patterns)} hardware patterns via I2C (interval: {interval}s).")
    print("Press Ctrl+C to stop.")
    
    idx = 0
    try:
        while True:
            name, pat_idx = hardware_patterns[idx]
            print(f"Setting hardware pattern: {name} (index {pat_idx})")
            set_dlp_pattern(bus_num, pat_idx)
            idx = (idx + 1) % len(hardware_patterns)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nExiting hardware loop.")
        # Restore parallel video input (0x00) on exit
        print("Restoring DLP to parallel RGB video input mode...")
        set_dlp_source(bus_num, 0)
        print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Loop through pattern signals on DLP2000.")
    parser.add_argument("--interval", type=float, default=1.5, help="Time in seconds per pattern (default: 1.5)")
    parser.add_argument("--internal", action="store_true", help="Loop using the projector's internal I2C patterns (default: Pygame screen loop)")
    args = parser.parse_args()
    
    if args.internal:
        run_hardware_loop(args.interval)
    else:
        # Before software loop, make sure DLP is set to parallel RGB input (0x00)
        bus_num = find_dlp_i2c_bus()
        try:
            print("Ensuring DLP is configured for parallel RGB input...")
            set_dlp_source(bus_num, 0)
        except Exception as e:
            print(f"Warning: Could not check/set DLP I2C source mode: {e}")
        run_software_loop(args.interval)

if __name__ == "__main__":
    main()
