#!/bin/bash
# Convert image path to absolute path
IMAGE_PATH="/home/jmunozbolanos/.gemini/antigravity-cli/brain/a73666c4-40da-4c9e-99f0-f6c67a7c3a42/calibration_image_1781707521095.jpg"

if [ -n "$1" ]; then
    IMAGE_PATH="$(realpath "$1")"
fi

if [ ! -f "$IMAGE_PATH" ]; then
    echo "Error: Image file not found at $IMAGE_PATH"
    exit 1
fi

echo "Displaying image: $IMAGE_PATH"
echo "Launching Chromium on extended display (DPI-1 at 1920,0)..."

# Set display variables for GUI session
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0

# Launch chromium in isolated kiosk mode
chromium \
  --user-data-dir=/tmp/chromium-projector \
  --window-position=1920,0 \
  --window-size=640,360 \
  --kiosk \
  "file://$IMAGE_PATH" &

echo "Chromium launched in background. Close the window on screen or kill the process to stop."
