from PIL import Image
import os

def process_for_evm(input_path, output_path):
    """
    Converts an input image to the exact format required by the DLPDLCR160CPEVM:
    640x360 resolution, 24-bit RGB, saved as a BMP.
    """
    # Open the image
    with Image.open(input_path) as img:
        # Convert to RGB (24-bit color) to ensure no alpha channel or palette
        img = img.convert("RGB")
        
        # Resize to 640x360 (nHD)
        # Using LANCZOS for high-quality downsampling/upsampling
        img_resized = img.resize((640, 360), Image.Resampling.LANCZOS)
        
        # Save explicitly as BMP
        img_resized.save(output_path, format="BMP")
        print(f"Saved: {output_path}")

def generate_zone_plate(output_path):
    """
    Generates a 640x360 interference pattern (zone plate) and saves it as a 24-bit BMP.
    """
    import numpy as np
    
    W, H = 640, 360
    
    # Create coordinate grids
    x = np.linspace(-W/2, W/2, W)
    y = np.linspace(-H/2, H/2, H)
    X, Y = np.meshgrid(x, y)
    
    R = np.sqrt(X**2 + Y**2)
    # Generate the pattern
    Z = np.sin(R**2 * 0.008) * 127.5 + 127.5
    
    # Map to an RGB array
    img_array = np.zeros((H, W, 3), dtype=np.uint8)
    img_array[:, :, 0] = Z          # Red channel
    img_array[:, :, 1] = Z          # Green channel
    img_array[:, :, 2] = 255 - Z    # Blue channel (inverted)
    
    img = Image.fromarray(img_array, 'RGB')
    img.save(output_path, format="BMP")
    print(f"Generated pattern: {output_path}")

# Example Usage:
# Convert an existing image
# process_for_evm("my_photo.jpg", "image1.bmp")

# Generate a test pattern
# generate_zone_plate("pattern.bmp")