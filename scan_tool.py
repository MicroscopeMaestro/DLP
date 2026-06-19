#!/usr/bin/env python3
import os
import sys
import time
import csv
from datetime import datetime

# Add the script's directory to python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

try:
    from NIRS import NIRS
except ImportError as e:
    print(f"Error importing NIRS wrapper: {e}")
    sys.exit(1)

def print_ascii_art():
    print("""
=========================================================
     Texas Instruments DLP NIRscan Nano - Scan Utility
=========================================================
""")

def check_connection():
    try:
        nirs = NIRS()
        ver = nirs.display_version()
        if ver != -1:
            return nirs
    except Exception:
        pass
    return None

def draw_ascii_chart(wavelengths, intensities):
    if not wavelengths or not intensities:
        return
    
    # Resample to 20 points for a simple ASCII plot
    num_points = 20
    step = max(1, len(wavelengths) // num_points)
    plot_w = wavelengths[::step][:num_points]
    plot_i = intensities[::step][:num_points]
    
    min_i, max_i = min(plot_i), max(plot_i)
    range_i = max_i - min_i if max_i != min_i else 1
    
    print("\n--- Approximate Intensity Profile ---")
    for w, val in zip(plot_w, plot_i):
        bar_len = int((val - min_i) / range_i * 40)
        bar = "#" * bar_len
        print(f"{w:6.1f} nm | {bar:<40} ({val})")
    print("--------------------------------------\n")

def main():
    print_ascii_art()
    
    print("Searching for NIRscan Nano device...")
    nirs = check_connection()
    
    if not nirs:
        print("\n[!] NIRscan Nano NOT detected.")
        print("Please check that:")
        print(" 1. The device is powered on (the green light should be flashing or solid).")
        print(" 2. The device is connected to this machine via USB.")
        print(" 3. The udev rules have been applied correctly.")
        print("\nWaiting for device to be plugged in... (Press Ctrl+C to exit)")
        
        while not nirs:
            try:
                time.sleep(1.5)
                nirs = check_connection()
                if nirs:
                    print("\n[+] NIRscan Nano detected successfully!")
                    break
            except KeyboardInterrupt:
                print("\nExiting scan utility.")
                sys.exit(0)
    else:
        print("[+] NIRscan Nano detected successfully!")

    try:
        # Get configuration details
        print("\nDevice Version:", nirs.display_version())
        
        # Reset error state
        nirs.clear_error_status()
        
        # Turn lamp on
        print("Turning on the lamp...")
        nirs.set_lamp_on_off(True)
        print("Allowing lamp to warm up for 3 seconds...")
        time.sleep(3)
        
        # Scan parameters
        # config index, type (1 = Hadamard), patterns, repeats, start, end, px width
        nirs.set_config(8, NIRS.TYPES.HADAMARD_TYPE, 228, 6, 900, 1700, 7)
        
        print("\nPerforming NIR scan...")
        nirs.scan()
        
        print("Retrieving scan results...")
        results = nirs.get_scan_results()
        
        # Turn lamp off
        nirs.set_lamp_on_off(False)
        print("Lamp turned off.")
        
        if not results or results.get("valid_length", 0) == 0:
            print("\n[!] No scan data retrieved or scan failed.")
            return

        print("\n================== Scan Results ==================")
        print(f"System Temperature:   {results.get('temperature_system', 0.0):.2f} °C")
        print(f"Detector Temperature: {results.get('temperature_detector', 0.0):.2f} °C")
        print(f"Humidity:             {results.get('humidity', 0.0):.2f} %")
        print(f"PGA Gain:             {results.get('pga', 0)}")
        print(f"Data Points Count:    {results.get('valid_length', 0)}")
        
        wavelengths = results.get("wavelength", [])
        intensities = results.get("intensity", [])
        references = results.get("reference", [])
        
        if wavelengths and intensities:
            draw_ascii_chart(wavelengths, intensities)
            
            # Calculate reflectance values
            reflectance = []
            for i, r in zip(intensities, references):
                if r != 0:
                    reflectance.append(float(i) / float(r))
                else:
                    reflectance.append(0.0)

            # Save data to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nir_scan_{timestamp}.csv"
            
            filepath = os.path.join(os.getcwd(), filename)
            with open(filepath, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Wavelength (nm)", "Intensity", "Reference", "Reflectance"])
                for w, i, r, ref_ratio in zip(wavelengths, intensities, references, reflectance):
                    writer.writerow([w, i, r, ref_ratio])
            
            print(f"[+] Full scan data successfully saved to: {filename}")
        
    except KeyboardInterrupt:
        print("\nScan aborted by user.")
    finally:
        # Make sure lamp is turned off on exit
        try:
            nirs.set_lamp_on_off(False)
        except:
            pass

if __name__ == "__main__":
    main()
