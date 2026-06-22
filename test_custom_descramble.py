#!/usr/bin/env python3
import os
import sys
import numpy as np

# Force window positioning environment variables before importing pygame
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

# Set display variables for GUI session
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'
if 'WAYLAND_DISPLAY' not in os.environ:
    os.environ['WAYLAND_DISPLAY'] = 'wayland-0'

try:
    import pygame
except ImportError:
    print("Error: pygame is not installed. Please run: pip install pygame")
    sys.exit(1)

DLP_W = 640
DLP_H = 360

def descramble_colors(img_rgb: np.ndarray) -> np.ndarray:
    """
    Descramble colors from target RGB space to the permuted physical wiring space.
    Input image is expected to have shape (H, W, 3) in RGB layout with values 0-255.
    """
    # Downshift to 6-bit channels
    R = (img_rgb[:, :, 0] >> 2).astype(np.uint8)
    G = (img_rgb[:, :, 1] >> 2).astype(np.uint8)
    B = (img_rgb[:, :, 2] >> 2).astype(np.uint8)

    # 1. Blue out matches Blue target (GPIO 4-9 map 1:1 to DLP LCD_DATA 0-5)
    b_out = B

    # 2. Compute r_out (RPi GPIO 16-21)
    #   r_out[0] = R_target[4]  =>  (R & 0x10) >> 4
    #   r_out[1] = R_target[5]  =>  (R & 0x20) >> 4
    #   r_out[2] = G_target[2]  =>  (G & 0x04)
    #   r_out[3] = G_target[3]  =>  (G & 0x08)
    #   r_out[4] = G_target[0]  =>  (G & 0x01) << 4
    #   r_out[5] = G_target[1]  =>  (G & 0x02) << 4
    r_out = np.zeros_like(R)
    r_out |= ((R & 0x10) >> 4)
    r_out |= ((R & 0x20) >> 4)
    r_out |= (G & 0x04)
    r_out |= (G & 0x08)
    r_out |= ((G & 0x01) << 4)
    r_out |= ((G & 0x02) << 4)

    # 3. Compute g_out (RPi GPIO 10-15)
    #   g_out[0] = G_target[4]  =>  (G & 0x10) >> 4
    #   g_out[1] = G_target[5]  =>  (G & 0x20) >> 4
    #   g_out[2] = R_target[0]  =>  (R & 0x01) << 2
    #   g_out[3] = R_target[1]  =>  (R & 0x02) << 2
    #   g_out[4] = R_target[2]  =>  (R & 0x04) << 2
    #   g_out[5] = R_target[3]  =>  (R & 0x08) << 2
    g_out = np.zeros_like(G)
    g_out |= ((G & 0x10) >> 4)
    g_out |= ((G & 0x20) >> 4)
    g_out |= ((R & 0x01) << 2)
    g_out |= ((R & 0x02) << 2)
    g_out |= ((R & 0x04) << 2)
    g_out |= ((R & 0x08) << 2)

    # Reconstruct 8-bit image for Pygame display
    out_rgb = np.zeros_like(img_rgb)
    out_rgb[:, :, 0] = r_out << 2
    out_rgb[:, :, 1] = g_out << 2
    out_rgb[:, :, 2] = b_out << 2
    
    return out_rgb

def generate_test_checkerboard() -> np.ndarray:
    """Generate a 640x360 diagnostic pattern containing various primary and secondary colors."""
    img = np.zeros((DLP_H, DLP_W, 3), dtype=np.uint8)
    
    # Divide into 8 horizontal bands/blocks
    block_w = DLP_W // 8
    
    # 8 standard colors (Red, Green, Blue, White, Black, Yellow, Cyan, Magenta)
    colors = [
        (252, 0, 0),      # Pure Red
        (0, 252, 0),      # Pure Green
        (0, 0, 252),      # Pure Blue
        (252, 252, 252),  # Pure White
        (0, 0, 0),        # Pure Black
        (252, 252, 0),    # Yellow (R+G)
        (0, 252, 252),    # Cyan (G+B)
        (252, 0, 252)     # Magenta (R+B)
    ]
    
    # Draw vertical color bars
    for i, color in enumerate(colors):
        x_start = i * block_w
        x_end = (i + 1) * block_w if i < 7 else DLP_W
        img[:, x_start:x_end] = color

    # Draw a black and white checkerboard in the bottom half of the image
    square_size = 40
    for y in range(DLP_H // 2, DLP_H, square_size):
        for x in range(0, DLP_W, square_size):
            if ((x // square_size) + (y // square_size)) % 2 == 0:
                img[y:y+square_size, x:x+square_size] = (252, 252, 252)  # White
            else:
                img[y:y+square_size, x:x+square_size] = (0, 0, 0)        # Black

    return img

def main():
    use_image = False
    image_path = ""
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--help", "-h"):
            print("Usage: python3 test_custom_descramble.py [optional_path_to_image]")
            sys.exit(0)
        else:
            image_path = sys.argv[1]
            use_image = True
            
    # Step 1: Create or load target image
    if use_image:
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            sys.exit(1)
        print(f"Loading image: {image_path}")
        # Use pygame to load to easily get rgb
        try:
            target_surf = pygame.image.load(image_path)
            target_surf = pygame.transform.smoothscale(target_surf, (DLP_W, DLP_H))
            # Convert surface to 3D numpy array
            target_img = pygame.surfarray.array3d(target_surf)
            # pygame surfarray is shape (W, H, 3) - we need to transpose to (H, W, 3)
            target_img = np.transpose(target_img, (1, 0, 2))
        except Exception as e:
            print(f"Error decoding image with Pygame: {e}")
            sys.exit(1)
    else:
        print("No image provided. Generating standard diagnostic color bars pattern...")
        target_img = generate_test_checkerboard()

    # Step 2: Apply the descramble mapping
    print("Applying custom hardware pinout descrambler...")
    descrambled_img = descramble_colors(target_img)

    # Step 3: Initialize Pygame
    print("Initializing display on DPI-1...")
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((DLP_W, DLP_H), pygame.NOFRAME)

    # Convert the numpy image back to a pygame surface
    # pygame expects (W, H, 3) for make_surface
    pygame_img_data = np.transpose(descrambled_img, (1, 0, 2))
    display_surf = pygame.surfarray.make_surface(pygame_img_data)

    print("Projection active! Press ESC or 'q' to exit.")
    running = True
    clock = pygame.time.Clock()
    
    # Toggle mode: press Space to toggle between descrambled and raw (original) scrambled projection
    show_descrambled = True
    
    # Re-transpose target image for pygame surface if raw is shown
    raw_img_data = np.transpose(target_img, (1, 0, 2))
    raw_surf = pygame.surfarray.make_surface(raw_img_data)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    show_descrambled = not show_descrambled
                    print(f"Switched display to: {'DESCRAMBLED (Correct Colors)' if show_descrambled else 'RAW (Scrambled Colors)'}")

        if show_descrambled:
            screen.blit(display_surf, (0, 0))
        else:
            screen.blit(raw_surf, (0, 0))
            
        pygame.display.flip()
        clock.tick(15)

    pygame.quit()
    print("Exited successfully.")

if __name__ == "__main__":
    main()
