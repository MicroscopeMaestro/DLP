#!/usr/bin/env python3
import os
import sys
import glob
import json
import logging
import numpy as np
from flask import Flask, jsonify, request, render_template, send_from_directory
from werkzeug.utils import secure_filename

# Silence Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, template_folder='templates', static_folder='static')
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Standard NIR Band Assignment database (900nm - 1700nm)
NIR_BANDS = [
    {"min": 900, "max": 930, "molecule": "C-H", "assignment": "3rd Overtone C-H (Alkanes, Methyl/Methylene groups, Starch)"},
    {"min": 930, "max": 980, "molecule": "O-H", "assignment": "3rd Overtone O-H (Water, Alcohols, Carbohydrates near 960-970nm)"},
    {"min": 980, "max": 1030, "molecule": "N-H", "assignment": "2nd Overtone N-H (Proteins, Amino Acids, Urea)"},
    {"min": 1030, "max": 1100, "molecule": "C-H / O-H", "assignment": "Combination Bands (Cellulose, Sugars, Starch)"},
    {"min": 1100, "max": 1250, "molecule": "C-H", "assignment": "2nd Overtone C-H (Fats, Lipids, Hydrocarbons, Oils near 1200-1215nm)"},
    {"min": 1250, "max": 1350, "molecule": "C-H / N-H", "assignment": "Combination/Overtones (Carbohydrates, Resins, Polyurethanes)"},
    {"min": 1350, "max": 1460, "molecule": "O-H / N-H", "assignment": "1st Overtone O-H & N-H (Water near 1440-1450nm, Starch, Proteins)"},
    {"min": 1460, "max": 1600, "molecule": "N-H", "assignment": "1st Overtone N-H (Proteins, Urea, Amides, Peptides near 1510-1530nm)"},
    {"min": 1600, "max": 1700, "molecule": "C-H", "assignment": "1st Overtone C-H (Starch, Cellulose, Methylene/Lipids near 1620-1650nm)"}
]

def get_closest_band(wavelength):
    """Find the closest molecular band assignment for a given wavelength."""
    closest = None
    min_dist = float('inf')
    
    # Check exact ranges first
    for band in NIR_BANDS:
        if band["min"] <= wavelength <= band["max"]:
            return band
            
    # If not in range, find the nearest boundary
    for band in NIR_BANDS:
        dist = min(abs(wavelength - band["min"]), abs(wavelength - band["max"]))
        if dist < min_dist:
            min_dist = dist
            closest = band
            
    return closest

# Custom pure-numpy Savitzky-Golay Filter
def savgol_filter(y, window_size, polyorder, deriv=0):
    if window_size % 2 == 0:
        window_size += 1  # force odd window size
    if polyorder >= window_size:
        polyorder = window_size - 1
        
    half_window = (window_size - 1) // 2
    order_range = np.arange(polyorder + 1)
    A = np.arange(-half_window, half_window + 1)[:, None] ** order_range
    pinv = np.linalg.pinv(A)
    coefs = pinv[deriv]
    
    # Pad borders to prevent shrink
    y_padded = np.pad(y, half_window, mode='edge')
    convolved = np.convolve(y_padded, coefs[::-1], mode='valid')
    return convolved

# Custom Moving Average Filter
def moving_average(y, window_size):
    if window_size < 1:
        return y
    half = window_size // 2
    y_padded = np.pad(y, half, mode='edge')
    weights = np.ones(window_size) / window_size
    return np.convolve(y_padded, weights, mode='valid')[:len(y)]

# Baseline Corrections
def apply_baseline_correction(y, method):
    y = np.array(y, dtype=float)
    if method == 'offset':
        # Subtract the minimum value (Offset correction)
        return y - np.min(y)
    elif method == 'snv':
        # Standard Normal Variate: (y - mean) / std
        std = np.std(y)
        if std == 0:
            return y - np.mean(y)
        return (y - np.mean(y)) / std
    elif method == 'minmax':
        # Normalize between 0 and 1
        ymin, ymax = np.min(y), np.max(y)
        range_y = ymax - ymin
        if range_y == 0:
            return np.zeros_like(y)
        return (y - ymin) / range_y
    return y  # None

# Peak and Valley Detectors
def detect_peaks_valleys(x, y, peak_type='peaks', threshold_factor=0.3):
    """Identify peaks or valleys in a spectrum."""
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    results = []
    
    # Simple relative local search
    indices = []
    if peak_type == 'peaks':
        # Peak: y[i] > adjacent points and y[i] is in the upper part
        ymin, ymax = np.min(y), np.max(y)
        min_threshold = ymin + (ymax - ymin) * threshold_factor
        for i in range(1, len(y) - 1):
            if y[i] > y[i-1] and y[i] > y[i+1]:
                if y[i] >= min_threshold:
                    indices.append(i)
    else: # valleys (typical absorption bands)
        # Valley: y[i] < adjacent points and y[i] is in the lower part
        ymin, ymax = np.min(y), np.max(y)
        max_threshold = ymax - (ymax - ymin) * threshold_factor
        for i in range(1, len(y) - 1):
            if y[i] < y[i-1] and y[i] < y[i+1]:
                if y[i] <= max_threshold:
                    indices.append(i)
                    
    for idx in indices:
        wl = x[idx]
        val = y[idx]
        band = get_closest_band(wl)
        results.append({
            "index": int(idx),
            "wavelength": float(wl),
            "value": float(val),
            "molecule": band["molecule"] if band else "Unknown",
            "assignment": band["assignment"] if band else "Unknown band overtone"
        })
        
    # Sort: peaks by value (descending), valleys by value (ascending)
    results.sort(key=lambda item: item["value"], reverse=(peak_type == 'peaks'))
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all CSV files in both parent scanning folder and uploads folder."""
    # Find CSV files in parent scanner folder
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    parent_csvs = glob.glob(os.path.join(parent_dir, "nir_scan_*.csv"))
    
    # Find CSV files in local uploads folder
    upload_csvs = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], "*.csv"))
    
    files = []
    for f in parent_csvs:
        files.append({
            "name": os.path.basename(f),
            "source": "scanner",
            "path": f
        })
    for f in upload_csvs:
        files.append({
            "name": os.path.basename(f),
            "source": "upload",
            "path": f
        })
        
    # Sort files by name descending (latest first)
    files.sort(key=lambda x: x["name"], reverse=True)
    return jsonify({"success": True, "files": files})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle custom file uploads."""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400
        
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"success": True, "message": f"File {filename} uploaded successfully."})
        
    return jsonify({"success": False, "message": "Only CSV files are supported."}), 400

@app.route('/api/process', methods=['POST'])
def process_spectra():
    """Processes multiple spectra with baseline correction, smoothing and peak detection."""
    data = request.json or {}
    files_to_load = data.get("files", [])
    baseline_methods = data.get("baselines", [])
    if not baseline_methods:
        single_baseline = data.get("baseline", "none")
        if single_baseline != "none":
            baseline_methods = [single_baseline]
    smoothing_method = data.get("smoothing", "none")
    sg_window = int(data.get("sg_window", 11))
    sg_poly = int(data.get("sg_poly", 2))
    ma_window = int(data.get("ma_window", 5))
    peak_type = data.get("peak_type", "valleys") # 'peaks' or 'valleys'
    threshold_factor = float(data.get("threshold_factor", 0.3))
    
    # For stack mode offsets
    stack_mode = bool(data.get("stack_mode", False))
    stack_offset = float(data.get("stack_offset", 0.15))
    
    results = {}
    
    for idx, f_info in enumerate(files_to_load):
        filepath = f_info.get("path")
        if not filepath or not os.path.exists(filepath):
            continue
            
        try:
            # Parse CSV file: assumes columns (Wavelength (nm), Intensity, Reference) or similar
            # Read all rows
            wavelengths = []
            intensities = []
            references = []
            reflectance = []
            
            with open(filepath, 'r') as csvfile:
                # Read header
                header_line = csvfile.readline().strip().lower()
                headers = [h.strip() for h in header_line.split(',')]
                
                # Identify index mappings
                w_idx, i_idx, r_idx = 0, 1, 2
                reflec_idx = None
                for i_col, col in enumerate(headers):
                    if 'wave' in col:
                        w_idx = i_col
                    elif 'intensity' in col:
                        i_idx = i_col
                    elif 'reflectance' in col:
                        reflec_idx = i_col
                    elif 'reference' in col or col == 'ref' or 'ref_val' in col:
                        r_idx = i_col
                
                # Read data
                for line in csvfile:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        try:
                            wl = float(parts[w_idx])
                            i_val = float(parts[i_idx])
                            
                            # Read pre-computed reflectance or calculate it from intensity and reference
                            if reflec_idx is not None and len(parts) > reflec_idx:
                                ref_val = float(parts[reflec_idx])
                            else:
                                r_val = float(parts[r_idx]) if len(parts) > r_idx else 0.0
                                if r_val != 0:
                                    ref_val = i_val / r_val
                                else:
                                    ref_val = 0.0
                                    
                            wavelengths.append(wl)
                            intensities.append(i_val)
                            reflectance.append(ref_val)
                        except ValueError:
                            continue # skip corrupt lines
            
            if not wavelengths:
                continue
                
            # Convert to numpy arrays
            x = np.array(wavelengths)
            y = np.array(reflectance)
            
            # Apply Baseline Correction in sequence
            y_base = y.copy()
            for method in baseline_methods:
                y_base = apply_baseline_correction(y_base, method)
            
            # Apply Smoothing
            if smoothing_method == 'savgol':
                y_proc = savgol_filter(y_base, sg_window, sg_poly)
            elif smoothing_method == 'moving_avg':
                y_proc = moving_average(y_base, ma_window)
            else:
                y_proc = y_base
                
            # Perform Peak/Valley Detection
            peaks = detect_peaks_valleys(x, y_proc, peak_type, threshold_factor)
            
            # If stack mode is active, apply vertical offset step
            y_display = y_proc.copy()
            if stack_mode:
                # Calculate vertical offset shift
                shift = idx * stack_offset
                y_display = y_display + shift
                
            results[f_info["name"]] = {
                "wavelengths": x.tolist(),
                "original_reflectance": y.tolist(),
                "processed_reflectance": y_proc.tolist(),
                "display_reflectance": y_display.tolist(),
                "peaks": peaks
            }
        except Exception as e:
            print(f"Error processing file {f_info['name']}: {e}")
            continue
            
    return jsonify({"success": True, "spectra": results})

if __name__ == '__main__':
    # Run the processing app on port 5001
    app.run(host='0.0.0.0', port=5001, debug=False)
