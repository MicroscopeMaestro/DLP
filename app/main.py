#!/usr/bin/env python3
import os
import sys
import time
import threading
import logging
import csv
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, render_template

# Silence Flask/werkzeug logging to save CPU console draw cycles
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Add parent directory to path to import NIRS
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from NIRS import NIRS
except ImportError as e:
    print(f"Error importing NIRS: {e}")
    sys.exit(1)

class SimulatedNIRS:
    def __init__(self):
        self.lamp_on = False
        self.hibernate = False
        self.pga = 1
        self.config = {
            "scan_type": 1,
            "num_patterns": 228,
            "num_repeats": 6,
            "wavelength_start": 900,
            "wavelength_end": 1700,
            "width_px": 7
        }
        self.slew_sections = []

    def display_version(self):
        return 9999

    def clear_error_status(self):
        return 0

    def set_lamp_on_off(self, new_value):
        self.lamp_on = bool(new_value)
        return 0

    def set_hibernate(self, new_value):
        self.hibernate = bool(new_value)
        return 0

    def set_pga_gain(self, new_value):
        self.pga = int(new_value)
        return 0

    def set_config(self, scanConfigIndex, scan_type, num_patterns, num_repeats, start, end, width):
        self.config = {
            "scan_type": scan_type,
            "num_patterns": num_patterns,
            "num_repeats": num_repeats,
            "wavelength_start": start,
            "wavelength_end": end,
            "width_px": width
        }
        return 0

    def set_slew_config(self, sections, num_repeats=6, scanConfigIndex=8):
        self.config["scan_type"] = 2
        self.config["num_repeats"] = num_repeats
        self.slew_sections = sections
        if sections:
            self.config["wavelength_start"] = sections[0].get("wavelength_start", 900)
            self.config["wavelength_end"] = sections[-1].get("wavelength_end", 1700)
            self.config["num_patterns"] = sum(s.get("num_patterns", 228) for s in sections)
        return 0

    def scan(self, num_repeats=1):
        # Simulate scan delay
        time.sleep(0.05 * num_repeats)
        return 0

    def get_scan_results(self):
        import random
        import math
        
        start = self.config.get("wavelength_start", 900)
        end = self.config.get("wavelength_end", 1700)
        num_pts = self.config.get("num_patterns", 228)
        
        num_pts = max(2, num_pts)
        wavelengths = [start + (end - start) * i / (num_pts - 1) for i in range(num_pts)]
        
        # Create a synthetic scan curve (water/starch/sugar peaks)
        intensities = []
        references = []
        for w in wavelengths:
            ref = 15000 - 0.03 * (w - 1300)**2 + random.randint(-150, 150)
            ref = max(1000, ref)
            references.append(int(ref))
            
            absorbance = 0.05
            absorbance += 0.4 * math.exp(-((w - 1445) / 50)**2)
            absorbance += 0.2 * math.exp(-((w - 1200) / 30)**2)
            absorbance += 0.15 * math.exp(-((w - 1020) / 25)**2)
            absorbance += random.uniform(-0.005, 0.005)
            
            val = ref * (1.0 - absorbance)
            intensities.append(int(max(0, val)))
            
        return {
            "temperature_system": round(25.0 + random.uniform(-0.5, 0.5), 2),
            "temperature_detector": round(23.5 + random.uniform(-0.3, 0.3), 2),
            "humidity": round(45.0 + random.uniform(-1.0, 1.0), 2),
            "pga": self.pga,
            "wavelength": wavelengths,
            "intensity": intensities,
            "reference": references,
            "valid_length": num_pts
        }

app = Flask(__name__, template_folder='templates', static_folder='static')

# Hardware Lock and state variables
hardware_lock = threading.Lock()
nirs_instance = None
last_interaction_time = time.time()
inactivity_timeout = 180.0  # Default 3 minutes (180 seconds)
lamp_state = False  # Keep track of lamp state (True = ON, False = OFF)
hibernation_capable = False  # Track device hibernation capability status
auto_secure_enabled = True  # Auto-secure watchdog status
latest_scan_results = None

# Cached environmental variables to avoid querying/parsing USB data on every poll
cached_temp_system = 0.0
cached_temp_detector = 0.0
cached_humidity = 0.0
cached_pga = 1
active_num_repeats = 6

def get_nirs_device():
    """Thread-safe instantiation and retrieval of NIRS hardware wrapper."""
    global nirs_instance
    if nirs_instance is None:
        try:
            # Try to connect to real hardware first
            nirs_instance = NIRS()
            ver = nirs_instance.display_version()
            if ver == -1:
                # Device not connected, fallback to simulated
                print("[Device] Physical NIRscan Nano not found. Initializing in Simulation Mode.")
                nirs_instance = SimulatedNIRS()
        except Exception as e:
            print(f"[Device] Exception initializing physical device ({e}). Falling back to Simulation Mode.")
            nirs_instance = SimulatedNIRS()
            
        # Retrieve once to pre-populate caches
        try:
            init_res = nirs_instance.get_scan_results()
            global cached_temp_system, cached_temp_detector, cached_humidity, cached_pga
            cached_temp_system = init_res.get("temperature_system", 0.0)
            cached_temp_detector = init_res.get("temperature_detector", 0.0)
            cached_humidity = init_res.get("humidity", 0.0)
            cached_pga = init_res.get("pga", 1)
        except Exception as cache_err:
            print(f"Failed to pre-populate telemetry caches: {cache_err}")
            
    return nirs_instance

def record_interaction():
    """Update the timestamp of the last hardware interaction."""
    global last_interaction_time
    last_interaction_time = time.time()

# Background watchdog thread to monitor inactivity
def inactivity_watchdog():
    global last_interaction_time, nirs_instance, lamp_state, auto_secure_enabled
    while True:
        time.sleep(5)
        if not auto_secure_enabled:
            continue
            
        elapsed = time.time() - last_interaction_time
        if elapsed > inactivity_timeout:
            # Device has been inactive for too long. Put in secure standby mode.
            with hardware_lock:
                device = get_nirs_device()
                if device:
                    try:
                        # Turn off the lamp if it's on
                        if lamp_state:
                            device.set_lamp_on_off(False)
                            lamp_state = False
                            print(f"[Watchdog] Inactivity timeout ({inactivity_timeout}s) exceeded. Lamp turned off automatically.")
                        
                        # Enable hibernation mode so device automatically sleeps
                        device.set_hibernate(True)
                        print(f"[Watchdog] Hibernation enabled automatically.")
                        
                        # Reset interaction time so we don't spam the console/hardware
                        record_interaction()
                    except Exception as e:
                        print(f"[Watchdog] Error putting device in secure standby: {e}")

# Start the watchdog thread in background
watchdog_thread = threading.Thread(target=inactivity_watchdog, daemon=True)
watchdog_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    global lamp_state, hibernation_capable
    with hardware_lock:
        device = get_nirs_device()
        if not device:
            return jsonify({
                "connected": False,
                "lamp_on": False,
                "hibernation_enabled": False,
                "message": "Device not connected."
            })
            
        try:
            version = device.display_version()
            is_sim = isinstance(device, SimulatedNIRS)
            
            return jsonify({
                "connected": True,
                "simulated": is_sim,
                "version_code": version,
                "lamp_on": lamp_state,
                "hibernation_enabled": hibernation_capable,
                "temperature_system": cached_temp_system,
                "temperature_detector": cached_temp_detector,
                "humidity": cached_humidity,
                "pga": cached_pga,
                "inactivity_seconds_left": max(0, inactivity_timeout - (time.time() - last_interaction_time)) if auto_secure_enabled else -1
            })
        except Exception as e:
            return jsonify({
                "connected": False,
                "message": f"Error retrieving device status: {str(e)}"
            })

@app.route('/api/connect', methods=['POST'])
def connect():
    global nirs_instance
    with hardware_lock:
        # Force recreation of the NIRS wrapper instance
        if nirs_instance:
            try:
                del nirs_instance
            except:
                pass
            nirs_instance = None
            
        device = get_nirs_device()
        record_interaction()
        if device:
            is_sim = isinstance(device, SimulatedNIRS)
            msg = "Successfully connected to Simulated NIRscan Nano!" if is_sim else "Successfully connected to NIRscan Nano!"
            return jsonify({"connected": True, "simulated": is_sim, "message": msg})
        else:
            return jsonify({"connected": False, "message": "Failed to connect. Make sure it is plugged in and powered on."})

@app.route('/api/config', methods=['POST'])
def configure():
    global active_num_repeats, cached_pga
    data = request.json or {}
    scan_type = int(data.get("scan_type", 1)) # 0: Column, 1: Hadamard
    num_patterns = int(data.get("num_patterns", 228))
    num_repeats = int(data.get("num_repeats", 6)) # averages
    wavelength_start = int(data.get("wavelength_start", 900))
    wavelength_end = int(data.get("wavelength_end", 1700))
    width_px = int(data.get("width_px", 7))
    pga_gain = int(data.get("pga_gain", 1))
    
    with hardware_lock:
        device = get_nirs_device()
        if not device:
            return jsonify({"success": False, "message": "Device not connected."}), 400
            
        try:
            device.clear_error_status()
            if scan_type == 2:
                section_scan_type = int(data.get("section_scan_type", 1))
                exposure_time = int(data.get("exposure_time", 1))
                sections = [{
                    "scan_type": section_scan_type,
                    "width_px": width_px,
                    "wavelength_start": wavelength_start,
                    "wavelength_end": wavelength_end,
                    "num_patterns": num_patterns,
                    "exposure_time": exposure_time
                }]
                print(f"[Config] Applying Slew Scan configuration: {sections}")
                device.set_slew_config(sections, num_repeats=num_repeats, scanConfigIndex=8)
            else:
                device.set_config(8, scan_type, num_patterns, num_repeats, wavelength_start, wavelength_end, width_px)
            device.set_pga_gain(pga_gain)
            
            # Update cache states immediately so dashboard displays updated parameters
            active_num_repeats = num_repeats
            cached_pga = pga_gain
            
            record_interaction()
            return jsonify({"success": True, "message": "Scan parameters updated successfully."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Configuration failed: {str(e)}"}), 500

@app.route('/api/scan', methods=['POST'])
def scan():
    global lamp_state, latest_scan_results
    data = request.json or {}
    auto_lamp = data.get("auto_lamp", True)
    warmup_time = float(data.get("warmup_time", 3.0))
    
    with hardware_lock:
        device = get_nirs_device()
        if not device:
            return jsonify({"success": False, "message": "Device not connected."}), 400
            
        try:
            record_interaction()
            device.clear_error_status()
            
            # If auto lamp control is checked, turn on lamp and warm up
            if auto_lamp and not lamp_state:
                device.set_lamp_on_off(True)
                lamp_state = True
                print(f"[Scan] Warming up lamp for {warmup_time}s...")
                time.sleep(warmup_time)
                
            # Perform scan with configured number of scans to average
            print(f"[Scan] Running scan with {active_num_repeats} averages...")
            device.scan(active_num_repeats)
            
            # Retrieve results
            results = device.get_scan_results()
            
            # Update cached telemetry parameters
            global cached_temp_system, cached_temp_detector, cached_humidity, cached_pga
            cached_temp_system = results.get("temperature_system", 0.0)
            cached_temp_detector = results.get("temperature_detector", 0.0)
            cached_humidity = results.get("humidity", 0.0)
            cached_pga = results.get("pga", 1)
            
            # Automatically turn off lamp if auto lamp control is checked
            if auto_lamp:
                device.set_lamp_on_off(False)
                lamp_state = False
                print("[Scan] Scan complete. Lamp turned off automatically.")
                
            # Compute reflectance
            wavelengths = results.get("wavelength", [])
            intensities = results.get("intensity", [])
            references = results.get("reference", [])
            
            reflectance = []
            for i, r in zip(intensities, references):
                if r != 0:
                    reflectance.append(float(i) / float(r))
                else:
                    reflectance.append(0.0)
                    
            results["reflectance"] = reflectance
            latest_scan_results = results
            
            # Save server-side CSV copy in the parent directory for the Chemometrics/Processing Studio
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"nir_scan_{timestamp}.csv"
                parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                filepath = os.path.join(parent_dir, filename)
                with open(filepath, mode="w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Wavelength (nm)", "Intensity", "Reference", "Reflectance"])
                    for w, i, r, ref_val in zip(wavelengths, intensities, references, reflectance):
                        writer.writerow([w, i, r, ref_val])
                print(f"[Scan] Saved server copy of scan: {filename}")
            except Exception as save_err:
                print(f"[Scan] Failed to save server-side CSV copy: {save_err}")
            
            record_interaction()
            return jsonify({
                "success": True,
                "results": results
            })
        except Exception as e:
            # Ensure lamp gets turned off if scan fails
            if auto_lamp:
                try:
                    device.set_lamp_on_off(False)
                    lamp_state = False
                except:
                    pass
            return jsonify({"success": False, "message": f"Scan execution failed: {str(e)}"}), 500

@app.route('/api/lamp', methods=['POST'])
def control_lamp():
    global lamp_state
    data = request.json or {}
    state = bool(data.get("state", False))
    
    with hardware_lock:
        device = get_nirs_device()
        if not device:
            return jsonify({"success": False, "message": "Device not connected."}), 400
            
        try:
            device.set_lamp_on_off(state)
            lamp_state = state
            record_interaction()
            return jsonify({"success": True, "message": f"Lamp turned {'ON' if state else 'OFF'} successfully."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Failed to toggle lamp: {str(e)}"}), 500

@app.route('/api/hibernate', methods=['POST'])
def control_hibernate():
    global hibernation_capable
    data = request.json or {}
    state = bool(data.get("state", False))
    
    with hardware_lock:
        device = get_nirs_device()
        if not device:
            return jsonify({"success": False, "message": "Device not connected."}), 400
            
        try:
            device.set_hibernate(state)
            hibernation_capable = state
            record_interaction()
            return jsonify({"success": True, "message": f"Hibernation {'enabled' if state else 'disabled'} successfully."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Failed to set hibernation: {str(e)}"}), 500

@app.route('/api/watchdog', methods=['POST'])
def control_watchdog():
    global auto_secure_enabled, inactivity_timeout
    data = request.json or {}
    auto_secure_enabled = bool(data.get("enabled", True))
    inactivity_timeout = float(data.get("timeout", 180.0))
    return jsonify({
        "success": True, 
        "message": f"Inactivity watchdog configured. Enabled: {auto_secure_enabled}, Timeout: {inactivity_timeout}s"
    })

@app.route('/api/secure_standby', methods=['POST'])
def trigger_secure_standby():
    global lamp_state
    with hardware_lock:
        device = get_nirs_device()
        if not device:
            return jsonify({"success": False, "message": "Device not connected."}), 400
            
        try:
            # Turn lamp off immediately
            device.set_lamp_on_off(False)
            lamp_state = False
            # Force enable hibernation
            device.set_hibernate(True)
            record_interaction()
            return jsonify({"success": True, "message": "Device successfully put in secure standby (lamp off, hibernation enabled)."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Failed to put device in secure standby: {str(e)}"}), 500

@app.route('/api/latest_scan', methods=['GET'])
def get_latest_scan():
    global latest_scan_results
    if latest_scan_results:
        return jsonify({"success": True, "results": latest_scan_results})
    else:
        return jsonify({"success": False, "message": "No scans recorded yet."}), 404

if __name__ == '__main__':
    # Run the server on port 5000, accessible inside/outside
    app.run(host='0.0.0.0', port=5000, debug=False)
