#!/usr/bin/env python3
import sys
import subprocess
import glob

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

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 change_pattern.py <pattern_index>")
        print("Standard pattern indices:")
        print("  0: Checkerboard")
        print("  1: Solid Color (usually default is black or white)")
        print("  2: Vertical Gray Ramp")
        print("  3: Horizontal Gray Ramp")
        print("  4: Grid (Crosshatch)")
        print("  5: Diagonal lines")
        print("  6: Vertical lines")
        print("  7: Horizontal lines")
        print("  8: Solid Color (another mode)")
        print("  12 (0x0C): Horizontal Gray Ramp (alt)")
        sys.exit(1)
        
    try:
        if sys.argv[1].startswith("0x"):
            pattern_index = int(sys.argv[1], 16)
        else:
            pattern_index = int(sys.argv[1])
    except ValueError:
        print("Error: Pattern index must be an integer (e.g. 4 or 0x04)")
        sys.exit(1)
        
    bus_num = find_dlp_i2c_bus()
    print(f"Using I2C software bus: {bus_num}")
    
    # 1st step: Set Input Source to Internal Test Pattern (0x01)
    subprocess.run(["i2cset", "-y", str(bus_num), "0x1b", "0x0b", "0x00", "0x00", "0x00", "0x01", "i"], check=True)
    
    # 2nd step: Write pattern selection to register 0x11 (32-bit block format)
    # The value is zero-padded as [0x00, 0x00, 0x00, pattern_index]
    pattern_bytes = [
        "0x00",
        "0x00",
        "0x00",
        f"0x{pattern_index:02X}"
    ]
    
    cmd = ["i2cset", "-y", str(bus_num), "0x1b", "0x11"] + pattern_bytes + ["i"]
    print(f"Applying pattern index {pattern_index} ({hex(pattern_index)})...")
    subprocess.run(cmd, check=True)
    print("Pattern applied successfully!")

if __name__ == "__main__":
    main()
