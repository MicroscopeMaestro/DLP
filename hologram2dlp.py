#%%
import numpy as np
import cv2
import os

def generate_grating_set(output_dir="dlp_gratings"):
    """
    Generates 24 green-channel binary gratings (4 periods x 6 angles).
    """
    # Create directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # DLPDLCR160CPEVM Native Resolution
    width = 640
    height = 360

    # Define the parameter matrix (4 periods * 6 angles = 24 images)
    periods_pixels = [8, 16, 32, 64] 
    angles_degrees = [0, 30, 60, 90, 120, 150] 

    # Create coordinate grid
    x = np.arange(width)
    y = np.arange(height)
    X, Y = np.meshgrid(x, y)

    image_counter = 1

    for p in periods_pixels:
        for ang in angles_degrees:
            # Convert angle to radians
            theta = np.radians(ang)

            # Rotate the coordinate system
            X_rot = X * np.cos(theta) + Y * np.sin(theta)

            # Generate binary grating along the rotated X-axis
            grating_binary = (X_rot % p < (p / 2)).astype(np.uint8)
            
            # Map to the Green channel (8-bit)
            G = grating_binary * 255
            R = np.zeros_like(G)
            B = np.zeros_like(G)

            # Stack channels (OpenCV uses BGR format)
            rgb_image = np.dstack((B, G, R))

            # Format filename to match imgN.bmp requirement for DLP controller
            filename = os.path.join(output_dir, f"img{image_counter}.bmp")
            
            # Save the image as uncompressed BMP (Explicitly setting NO compression)
            cv2.imwrite(filename, rgb_image, [cv2.IMWRITE_BMP_COMPRESSION, cv2.IMWRITE_BMP_COMPRESSION_RGB])
            print(f"Generated: {filename}")
            
            image_counter += 1
    # Generate conf.txt for the DLP EVM
    conf_filename = os.path.join(output_dir, "conf.txt")
    with open(conf_filename, "w") as f:
        f.write("boot_up_mode 2\n")
        f.write(f"number_of_sdcard_images {len(periods_pixels) * len(angles_degrees)}\n")
        
        # image_names: img1.bmp,img2.bmp,img3.bmp...
        image_names = ",".join([f"img{i}.bmp" for i in range(1, image_counter)])
        f.write(f"image_names {image_names}\n")
        
        f.write("sequence_repeat 1\n")
        f.write(f"number_of_sequence {(image_counter - 1) * 3}\n")
        
        for i in range(1, image_counter):
            f.write("rgb_fill 0,0,0\n")
            f.write(f"image {i},0,0\n")
            f.write("delay 500\n") # 500ms delay per image

    print(f"Generated: {conf_filename}")

if __name__ == "__main__":
    generate_grating_set()
# %%
