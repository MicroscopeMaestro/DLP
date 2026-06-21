#!/bin/bash
# dlp2000_init.sh - DLP2000EVM DLPC3430 I2C initialization for Raspberry Pi 5
# Requires: i2c-gpio overlay on GPIO23 (SDA) / GPIO24 (SCL)

sleep 2

# Find the i2c-gpio bus by checking for GPIO23 (SDA) in dmesg device registration
# On RPi5 the bus name is the DT node address (e.g. 400000002.i2c), not "gpio"
find_gpio_i2c_bus() {
    local name_file name bus_num
    # 1. Search for 'i2c-gpio' software bus first
    for name_file in /sys/class/i2c-dev/i2c-*/name; do
        if [ -f "$name_file" ]; then
            name=$(cat "$name_file")
            if [[ "$name" == *"i2c-gpio"* ]]; then
                bus_num=$(basename "$(dirname "$name_file")" | cut -d'-' -f2)
                echo "$bus_num"
                return 0
            fi
        fi
    done

    # 2. Search for any '*00000002.i2c' bus name
    for name_file in /sys/class/i2c-dev/i2c-*/name; do
        if [ -f "$name_file" ]; then
            name=$(cat "$name_file")
            if [[ "$name" =~ [0-9]+00000002\.i2c ]]; then
                bus_num=$(basename "$(dirname "$name_file")" | cut -d'-' -f2)
                echo "$bus_num"
                return 0
            fi
        fi
    done

    # 3. Fallback: check if /dev/i2c-5 or /dev/i2c-4 exists
    if [ -e /dev/i2c-5 ]; then
        echo "5"
        return 0
    elif [ -e /dev/i2c-4 ]; then
        echo "4"
        return 0
    fi
    return 1
}

BUS_NUM=$(find_gpio_i2c_bus)

if [ -z "$BUS_NUM" ]; then
    echo "ERROR: i2c-gpio bus with DLPC3430 at 0x1B not found." >&2
    echo "Check /boot/firmware/config.txt [all] section:" >&2
    echo "  dtoverlay=i2c-gpio,i2c_gpio_sda=23,i2c_gpio_scl=24,i2c_gpio_delay_us=2,bus=4" >&2
    exit 1
fi

I2C_ADDR=0x1b
echo "DLP2000EVM on i2c-$BUS_NUM — starting initialization..."

# 1. Freeze display buffer (prevents tearing during switch)
i2cset -y "$BUS_NUM" $I2C_ADDR 0xa3 0x00 0x00 0x00 0x01 i

# 2. Set input source to parallel DPI (640x360, nHD)
i2cset -y "$BUS_NUM" $I2C_ADDR 0x0c 0x00 0x00 0x00 0x1b i

# 3. Set pixel format to RGB666
i2cset -y "$BUS_NUM" $I2C_ADDR 0x0d 0x00 0x00 0x00 0x01 i

# 4. Enable display output
i2cset -y "$BUS_NUM" $I2C_ADDR 0x0b 0x00 0x00 0x00 0x00 i

# 5. Unfreeze display buffer (projection begins)
i2cset -y "$BUS_NUM" $I2C_ADDR 0xa3 0x00 0x00 0x00 0x00 i

echo "DLP2000EVM initialized on bus $BUS_NUM."
exit 0
