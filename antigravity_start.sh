#!/bin/bash
# antigravity_start.sh — runtime DLP2000EVM second-screen init (no boot changes)
# Based on: https://www.intellar.ca/blog/raspberry-pi-evm2000
# Run with: sudo bash antigravity_start.sh

set -e

DLP_I2C_SDA=23
DLP_I2C_SCL=24
DLPC_ADDR=0x1b
DLP_BUS_LABEL="i2c-gpio"

echo "[1/4] Loading DPI overlay (RGB666 640x360 @ 25MHz)..."
if dtoverlay -l | grep -q "vc4-kms-dpi-generic"; then
    echo "      Already loaded, skipping."
else
    dtoverlay vc4-kms-dpi-generic \
        clock-frequency=25000000 \
        hactive=640 hfp=14 hsync=4 hbp=12 \
        vactive=360 vfp=2 vsync=3 vbp=9
    echo "      Done."
fi

echo "[2/4] Loading software I2C overlay (GPIO${DLP_I2C_SDA}/GPIO${DLP_I2C_SCL})..."
if dtoverlay -l | grep -q "i2c-gpio"; then
    echo "      Already loaded, skipping."
else
    dtoverlay i2c-gpio \
        i2c_gpio_sda=${DLP_I2C_SDA} \
        i2c_gpio_scl=${DLP_I2C_SCL} \
        i2c_gpio_delay_us=2
    echo "      Done."
fi

echo "[3/4] Waiting for framebuffer and I2C bus..."
for i in $(seq 1 20); do
    [ -e /dev/fb1 ] && break
    sleep 0.5
done
[ -e /dev/fb1 ] || { echo "ERROR: /dev/fb1 not found after 10s. Check DPI wiring."; exit 1; }
echo "      Framebuffer: $(ls /dev/fb*)"

# Find the i2c-gpio bus number
I2C_BUS=""
for path in /sys/bus/i2c/devices/i2c-*/of_node/compatible; do
    if grep -q "$DLP_BUS_LABEL" "$path" 2>/dev/null; then
        BUS_DIR=$(dirname "$(dirname "$path")")
        I2C_BUS=$(basename "$BUS_DIR" | cut -d'-' -f2)
        break
    fi
done
[ -n "$I2C_BUS" ] || { echo "ERROR: i2c-gpio bus not found."; exit 1; }
echo "      I2C bus: /dev/i2c-${I2C_BUS}"

echo "[4/4] Initializing DLPC3430 (addr ${DLPC_ADDR})..."
# Set resolution: nHD 640x360 landscape (0x1B)
i2cset -y "$I2C_BUS" "$DLPC_ADDR" 0x0c 0x00 0x00 0x00 0x1B i
sleep 0.1
# Select parallel RGB input (0x00)
i2cset -y "$I2C_BUS" "$DLPC_ADDR" 0x0b 0x00 0x00 0x00 0x00 i
sleep 0.1
echo "      DLPC3430 initialized."

echo ""
echo "[5/5] Configuring display layout..."
# Wait for X to have the display before xrandr
for i in $(seq 1 20); do
    DISPLAY=:0 xrandr --listmonitors 2>/dev/null | grep -q "DPI" && break
    sleep 0.5
done

if DISPLAY=:0 xrandr --listmonitors 2>/dev/null | grep -q "DPI"; then
    DISPLAY=:0 xrandr \
        --output HDMI-A-1 --mode 1920x1080 --pos 0x0 --primary \
        --output DPI-1 --mode 640x360 --pos 1920x0 --brightness 1.0
    echo "      HDMI-A-1: 1920x1080 (primary)"
    echo "      DPI-1:    640x360 @ 1920,0 (DLP projector)"
else
    echo "      WARNING: DPI-1 not seen by X yet — run manually:"
    echo "      DISPLAY=:0 xrandr --output DPI-1 --mode 640x360 --pos 1920x0 --brightness 1.0"
fi

echo ""
echo "DLP2000EVM ready as second screen (/dev/fb1)."
echo ""
echo "Usage:"
echo "  Drag windows past right edge of main screen → appears on DLP"
echo "  Mirror screen:  python3 ~/DLP/screen_mirror.py --no-init"
echo "  Test pattern:   python3 ~/DLP/show_random.py --animate --no-init"
