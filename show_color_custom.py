#!/usr/bin/env python3
"""
Display a solid color on the projector, corrected for custom wiring (Option C).
Usage:
  python3 show_color_custom.py green
  python3 show_color_custom.py red
  python3 show_color_custom.py blue
  python3 show_color_custom.py white
  python3 show_color_custom.py 0 252 0
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
    print("Error: pygame is not installed. Run: pip install pygame")
    sys.exit(1)

# Color name mapping
COLORS = {
    "red": (252, 0, 0),
    "green": (0, 252, 0),
    "blue": (0, 0, 252),
    "white": (252, 252, 252),
    "black": (0, 0, 0),
    "yellow": (252, 252, 0),
    "cyan": (0, 252, 252),
    "magenta": (252, 0, 252),
}

def descramble_color(r_in: int, g_in: int, b_in: int) -> tuple:
    """Descramble standard RGB to custom Option C wiring GPIO output."""
    # Downshift to 6-bit channels
    R = r_in >> 2
    G = g_in >> 2
    B = b_in >> 2

    # Blue out maps 1:1
    b_out = B

    # Compute r_out (RPi GPIO 16-21)
    r_out = 0
    r_out |= ((R & 0x10) >> 4)
    r_out |= ((R & 0x20) >> 4)
    r_out |= (G & 0x04)
    r_out |= (G & 0x08)
    r_out |= ((G & 0x01) << 4)
    r_out |= ((G & 0x02) << 4)

    # Compute g_out (RPi GPIO 10-15)
    g_out = 0
    g_out |= ((G & 0x10) >> 4)
    g_out |= ((G & 0x20) >> 4)
    g_out |= ((R & 0x01) << 2)
    g_out |= ((R & 0x02) << 2)
    g_out |= ((R & 0x04) << 2)
    g_out |= ((R & 0x08) << 2)

    # Upscale back to 8-bit
    return (r_out << 2, g_out << 2, b_out << 2)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 show_color_custom.py <color_name>")
        print("  python3 show_color_custom.py <R> <G> <B>")
        print("\nAvailable color names:", ", ".join(COLORS.keys()))
        sys.exit(1)

    arg1 = sys.argv[1].lower()
    if arg1 in COLORS:
        target_color = COLORS[arg1]
        color_name = arg1
    else:
        try:
            r = int(sys.argv[1])
            g = int(sys.argv[2])
            b = int(sys.argv[3])
            target_color = (r, g, b)
            color_name = f"RGB({r},{g},{b})"
        except (ValueError, IndexError):
            print(f"Error: Unknown color or invalid RGB values: {sys.argv[1:]}")
            sys.exit(1)

    # Apply the descrambling correction
    corrected_color = descramble_color(*target_color)

    print(f"Target color: {color_name} {target_color}")
    print(f"Applying software correction -> Sending {corrected_color} to Pygame")

    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((640, 360), pygame.FULLSCREEN | pygame.NOFRAME)

    # Fill screen with corrected color
    screen.fill(corrected_color)
    pygame.display.flip()

    print("Solid color screen active. Press ESC or 'q' to exit.")
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
