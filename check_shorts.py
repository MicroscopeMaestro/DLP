#!/usr/bin/env python3
import subprocess
import time
import sys

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return result.stdout.strip()

def main():
    print("====================================================")
    # 1. Read current pinctrl states for backup
    print("Backing up current pin configurations...")
    backup = run_cmd("pinctrl get 4-9,16-21")
    print(backup)
    print("----------------------------------------------------")

    # 2. Configure Red pins (16-21) as outputs
    # and Blue pins (4-9) as inputs with pull-downs (to avoid floating reads)
    print("Configuring Red (GPIO 16-21) as outputs and Blue (GPIO 4-9) as inputs...")
    for pin in range(16, 22):
        run_cmd(f"pinctrl set {pin} op")
    for pin in range(4, 10):
        run_cmd(f"pinctrl set {pin} ip pd")
    
    time.sleep(0.1)

    # 3. Test 1: Drive all Red pins LOW
    print("\n--- Test 1: Driving Red pins LOW ---")
    for pin in range(16, 22):
        run_cmd(f"pinctrl set {pin} dl")
    time.sleep(0.1)
    
    blue_low_states = {}
    for pin in range(4, 10):
        state = run_cmd(f"pinctrl get {pin}")
        # Parse 'lo' or 'hi'
        is_high = "hi" in state
        blue_low_states[pin] = "HIGH" if is_high else "LOW"
    
    for pin, state in blue_low_states.items():
        print(f"  GPIO {pin} (Blue pin) reads: {state}")

    # 4. Test 2: Drive all Red pins HIGH
    print("\n--- Test 2: Driving Red pins HIGH ---")
    for pin in range(16, 22):
        run_cmd(f"pinctrl set {pin} dh")
    time.sleep(0.1)
    
    blue_high_states = {}
    shorts_detected = []
    for pin in range(4, 10):
        state = run_cmd(f"pinctrl get {pin}")
        is_high = "hi" in state
        blue_high_states[pin] = "HIGH" if is_high else "LOW"
        if is_high:
            shorts_detected.append(pin)
            
    for pin, state in blue_high_states.items():
        print(f"  GPIO {pin} (Blue pin) reads: {state}")

    print("----------------------------------------------------")
    if shorts_detected:
        print("⚠️  WARNING: Electrical short/bridge detected!")
        print(f"The following Blue pins read HIGH when Red was turned on: {shorts_detected}")
        print("This indicates those pins are electrically connected (shorted) to a Red signal wire.")
    else:
        print("✅ No direct short-circuits detected between Red and Blue GPIO pins.")
        print("If Red still looks purple, it is likely that the wires are plugged into incorrect pins.")

    # 5. Restore original configurations (return to ALT1/DPI)
    print("\nRestoring pin configurations...")
    for pin in range(4, 10):
        run_cmd(f"pinctrl set {pin} a1")
    for pin in range(16, 22):
        run_cmd(f"pinctrl set {pin} a1")
    print("Done. DPI mode restored.")
    print("====================================================")

if __name__ == "__main__":
    main()
