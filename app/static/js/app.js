// TI DLP NIRscan Nano Dashboard JavaScript Frontend Logic
document.addEventListener("DOMContentLoaded", () => {
    
    // UI Elements Selection
    const elConnectionStatus = document.getElementById("connection-status");
    const elStatusText = document.getElementById("status-text");
    const btnReconnect = document.getElementById("btn-reconnect");
    
    const chkWatchdog = document.getElementById("chk-watchdog");
    const rngTimeout = document.getElementById("rng-timeout");
    const lblTimeout = document.getElementById("lbl-timeout");
    const chkHibernate = document.getElementById("chk-hibernate");
    const lblCountdown = document.getElementById("lbl-countdown");
    const btnSecure = document.getElementById("btn-secure");
    
    const selScanType = document.getElementById("sel-scan-type");
    const numRepeats = document.getElementById("num-repeats");
    const rowExposureTime = document.getElementById("row-exposure-time");
    const exposureTime = document.getElementById("exposure-time");
    const wavelengthStart = document.getElementById("wavelength-start");
    const wavelengthEnd = document.getElementById("wavelength-end");
    const numPatterns = document.getElementById("num-patterns");
    const widthPx = document.getElementById("width-px");
    const pgaGain = document.getElementById("pga-gain");
    const btnSaveConfig = document.getElementById("btn-save-config");
    
    const chkLamp = document.getElementById("chk-lamp");
    const chkAutoLamp = document.getElementById("chk-auto-lamp");
    const warmupSettingGroup = document.getElementById("warmup-setting-group");
    const rngWarmup = document.getElementById("rng-warmup");
    const lblWarmup = document.getElementById("lbl-warmup");
    const btnScan = document.getElementById("btn-scan");
    const btnScanText = document.getElementById("btn-scan-text");
    const btnScanLoader = document.getElementById("btn-scan-loader");
    
    const valTempSystem = document.getElementById("val-temp-system");
    const valHumidity = document.getElementById("val-humidity");
    const valPgaGain = document.getElementById("val-pga-gain");
    
    const tabReflectance = document.getElementById("tab-reflectance");
    const tabReconstructed = document.getElementById("tab-reconstructed");
    const valScanTimestamp = document.getElementById("val-scan-timestamp");
    const valDataPoints = document.getElementById("val-data-points");
    const btnExportCsv = document.getElementById("btn-export-csv");
    
    const logTerminal = document.getElementById("log-terminal");
    const btnClearLogs = document.getElementById("btn-clear-logs");

    // Local Variables
    let isConnected = false;
    let scanChart = null;
    let latestScanData = null;
    let activeTab = "reflectance"; // 'reflectance' or 'reconstructed'
    let countdownInterval = null;

    // Initialize Chart.js
    function initChart() {
        const ctx = document.getElementById('spectrumChart').getContext('2d');
        
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
        
        scanChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        boxPadding: 6,
                        usePointStyle: true
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Wavelength (nm)',
                            font: {
                                size: 13,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.05)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Value',
                            font: {
                                size: 13,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.05)'
                        }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            }
        });
    }

    // Write Log Entry
    function log(message, type = "info") {
        const entry = document.createElement("div");
        entry.className = `log-entry log-${type}`;
        
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];
        entry.textContent = `[${timeStr}] ${message}`;
        
        logTerminal.appendChild(entry);
        logTerminal.scrollTop = logTerminal.scrollHeight;
    }

    // Sync UI with connection status
    function setConnectionState(state, infoMsg = "") {
        if (state === "connected" || state === "simulated") {
            isConnected = true;
            if (state === "simulated") {
                elConnectionStatus.className = "status-badge status-simulated";
                elStatusText.textContent = "Simulated";
            } else {
                elConnectionStatus.className = "status-badge status-connected";
                elStatusText.textContent = "Connected";
            }
            btnScan.disabled = false;
            btnSaveConfig.disabled = false;
            chkLamp.disabled = false;
            chkHibernate.disabled = false;
        } else {
            isConnected = false;
            elConnectionStatus.className = "status-badge status-disconnected";
            elStatusText.textContent = "Disconnected";
            btnScan.disabled = true;
            btnSaveConfig.disabled = true;
            chkLamp.disabled = true;
            chkHibernate.disabled = true;
            
            // Reset fields
            valTempSystem.textContent = "--.- °C";
            valHumidity.textContent = "--.- %";
            valPgaGain.textContent = "--";
            
            if (infoMsg) log(infoMsg, "error");
        }
    }

    // Refresh Device Status (Telemetry)
    async function checkStatus() {
        try {
            const res = await fetch("/api/status");
            const status = await res.json();
            
            if (status.connected) {
                if (!isConnected) {
                    setConnectionState(status.simulated ? "simulated" : "connected");
                    if (status.simulated) {
                        log("NIRscan Nano initialized in SIMULATION Mode.", "info");
                    } else {
                        log("NIRscan Nano connected successfully.", "success");
                    }
                }
                
                // Update Telemetry Values
                valTempSystem.textContent = `${status.temperature_system.toFixed(2)} °C`;
                valHumidity.textContent = `${status.humidity.toFixed(2)} %`;
                valPgaGain.textContent = `${status.pga}x`;
                
                // Keep lamp checkbox synced (do not trigger toggle calls while updating checkbox status)
                chkLamp.checked = status.lamp_on;
                chkHibernate.checked = status.hibernation_enabled;
                
                // Watchdog countdown update
                if (status.inactivity_seconds_left >= 0) {
                    const secs = Math.ceil(status.inactivity_seconds_left);
                    lblCountdown.textContent = `${secs}s`;
                    if (secs <= 30) {
                        lblCountdown.style.color = "var(--accent-red)";
                    } else if (secs <= 60) {
                        lblCountdown.style.color = "var(--accent-yellow)";
                    } else {
                        lblCountdown.style.color = "var(--accent-cyan)";
                    }
                } else {
                    lblCountdown.textContent = "Disabled";
                    lblCountdown.style.color = "var(--text-muted)";
                }
            } else {
                if (isConnected) {
                    setConnectionState(false, "Device connection lost.");
                }
            }
        } catch (err) {
            console.error("Error checking status:", err);
        }
    }

    // Reconnect API call
    async function handleReconnect() {
        btnReconnect.disabled = true;
        log("Attempting to connect to hardware...", "info");
        try {
            const res = await fetch("/api/connect", { method: "POST" });
            const data = await res.json();
            
            if (data.connected) {
                setConnectionState(data.simulated ? "simulated" : "connected");
                log(data.message, "success");
                checkStatus();
            } else {
                setConnectionState(false);
                log(data.message, "error");
            }
        } catch (err) {
            log("Connection endpoint error.", "error");
        } finally {
            btnReconnect.disabled = false;
        }
    }

    // Auto-Standby Settings Update
    async function updateWatchdogConfig() {
        const enabled = chkWatchdog.checked;
        const timeout = parseFloat(rngTimeout.value);
        
        try {
            const res = await fetch("/api/watchdog", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled, timeout })
            });
            const data = await res.json();
            if (data.success) {
                log(`Watchdog configured: timeout ${timeout}s, enabled: ${enabled}`, "info");
            }
        } catch (err) {
            log("Failed to configure watchdog settings.", "error");
        }
    }

    // Apply configuration parameters
    async function applyParameters() {
        btnSaveConfig.disabled = true;
        
        const raw_scan_type = parseInt(selScanType.value);
        const num_patterns = parseInt(numPatterns.value);
        const num_repeats = parseInt(numRepeats.value);
        const wavelength_start = parseInt(wavelengthStart.value);
        const wavelength_end = parseInt(wavelengthEnd.value);
        const width_px = parseInt(widthPx.value);
        const pga_gain = parseInt(pgaGain.value);
        
        let scan_type = raw_scan_type;
        let section_scan_type = 1;
        let exposure_time = 1;
        
        if (raw_scan_type === 2 || raw_scan_type === 3) {
            scan_type = 2; // SLEW_TYPE
            section_scan_type = (raw_scan_type === 2) ? 1 : 0;
            exposure_time = parseInt(exposureTime.value);
            log(`Configuring Slew Scan mode: inner pattern type: ${section_scan_type === 1 ? 'Hadamard' : 'Column'}, exposure index: ${exposure_time}...`, "info");
        } else {
            log("Applying updated scan parameters to device EEPROM...", "info");
        }
        
        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    scan_type, section_scan_type, exposure_time, num_patterns, num_repeats, wavelength_start, wavelength_end, width_px, pga_gain
                })
            });
            const data = await res.json();
            
            if (data.success) {
                log(data.message, "success");
            } else {
                log(data.message, "error");
            }
        } catch (err) {
            log("Config endpoint error.", "error");
        } finally {
            btnSaveConfig.disabled = false;
            checkStatus();
        }
    }

    // Trigger Scan
    async function executeScan() {
        btnScan.disabled = true;
        btnScanText.className = "hidden";
        btnScanLoader.className = "";
        
        const auto_lamp = chkAutoLamp.checked;
        const warmup_time = parseFloat(rngWarmup.value);
        
        log("Starting spectrum acquisition...", "info");
        if (auto_lamp) {
            log(`Warming up infrared lamp for ${warmup_time}s...`, "info");
        }
        
        try {
            const res = await fetch("/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ auto_lamp, warmup_time })
            });
            const data = await res.json();
            
            if (data.success) {
                latestScanData = data.results;
                log("Scan complete. Retooling spectrum visualizer.", "success");
                
                // Display timestamp
                valScanTimestamp.innerHTML = `<i class="fa-regular fa-clock"></i> Scanned: ${new Date().toLocaleTimeString()}`;
                valDataPoints.textContent = `${latestScanData.valid_length} points`;
                
                btnExportCsv.disabled = false;
                
                // Render chart
                updateChart();
            } else {
                log(data.message, "error");
            }
        } catch (err) {
            log("Scan execution endpoint error.", "error");
        } finally {
            btnScan.disabled = false;
            btnScanText.className = "";
            btnScanLoader.className = "hidden";
            checkStatus();
        }
    }

    // Update Chart with latest data
    function updateChart() {
        if (!latestScanData) return;
        
        const wavelengths = latestScanData.wavelength || [];
        const xLabels = wavelengths.map(w => w.toFixed(1));
        
        scanChart.data.labels = xLabels;
        
        if (activeTab === "reflectance") {
            const reflectanceData = latestScanData.reflectance || [];
            
            scanChart.data.datasets = [{
                label: 'Reflectance Ratio (Sample/Ref)',
                data: reflectanceData,
                borderColor: '#22d3ee',
                backgroundColor: 'rgba(34, 211, 238, 0.08)',
                borderWidth: 2.5,
                tension: 0.15,
                pointRadius: 0.5,
                pointHoverRadius: 4,
                fill: true
            }];
            scanChart.options.scales.y.title.text = 'Reflectance';
        } else {
            const intensityData = latestScanData.intensity || [];
            const referenceData = latestScanData.reference || [];
            
            scanChart.data.datasets = [
                {
                    label: 'Sample Intensity (Reconstructed)',
                    data: intensityData,
                    borderColor: '#818cf8',
                    backgroundColor: 'rgba(129, 140, 248, 0.05)',
                    borderWidth: 2,
                    tension: 0.15,
                    pointRadius: 0.5,
                    pointHoverRadius: 4,
                    fill: false
                },
                {
                    label: 'Reference White Intensity',
                    data: referenceData,
                    borderColor: '#fbbf24',
                    backgroundColor: 'rgba(251, 191, 36, 0.05)',
                    borderWidth: 2,
                    tension: 0.15,
                    pointRadius: 0.5,
                    pointHoverRadius: 4,
                    fill: false
                }
            ];
            scanChart.options.scales.y.title.text = 'Raw Signal Counts';
        }
        
        scanChart.update();
    }

    // Manual Lamp Toggle
    async function toggleLamp() {
        const state = chkLamp.checked;
        log(`Manually setting lamp state to ${state ? 'ON' : 'OFF'}...`, "info");
        try {
            const res = await fetch("/api/lamp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ state })
            });
            const data = await res.json();
            if (data.success) {
                log(data.message, "success");
            } else {
                log(data.message, "error");
                chkLamp.checked = !state;
            }
        } catch (err) {
            log("Lamp toggle endpoint failure.", "error");
            chkLamp.checked = !state;
        }
    }

    // Toggle Hibernate capability
    async function toggleHibernate() {
        const state = chkHibernate.checked;
        log(`Setting hibernation allowance to ${state ? 'ENABLED' : 'DISABLED'}...`, "info");
        try {
            const res = await fetch("/api/hibernate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ state })
            });
            const data = await res.json();
            if (data.success) {
                log(data.message, "success");
            } else {
                log(data.message, "error");
                chkHibernate.checked = !state;
            }
        } catch (err) {
            log("Hibernate configuration failure.", "error");
            chkHibernate.checked = !state;
        }
    }

    // Trigger Secure Standby
    async function triggerSecureStandby() {
        btnSecure.disabled = true;
        log("Triggering immediate secure standby condition...", "warning");
        try {
            const res = await fetch("/api/secure_standby", { method: "POST" });
            const data = await res.json();
            
            if (data.success) {
                log(data.message, "success");
                chkLamp.checked = false;
                chkHibernate.checked = true;
                checkStatus();
            } else {
                log(data.message, "error");
            }
        } catch (err) {
            log("Secure standby endpoint failure.", "error");
        } finally {
            btnSecure.disabled = false;
        }
    }

    // Export Scan Data to CSV
    function exportToCSV() {
        if (!latestScanData) return;
        
        const wavelengths = latestScanData.wavelength || [];
        const intensities = latestScanData.intensity || [];
        const references = latestScanData.reference || [];
        const reflectance = latestScanData.reflectance || [];
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Wavelength (nm),Intensity,Reference,Reflectance\n";
        
        for (let i = 0; i < wavelengths.length; i++) {
            csvContent += `${wavelengths[i]},${intensities[i] || 0},${references[i] || 0},${reflectance[i] || 0}\n`;
        }
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        const timestamp = new Date().toISOString().slice(0,19).replace(/[:T]/g, "_");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `nir_scan_export_${timestamp}.csv`);
        document.body.appendChild(link);
        
        link.click();
        document.body.removeChild(link);
        log("Scan data CSV file downloaded.", "success");
    }

    // Add UI Listeners
    selScanType.addEventListener("change", () => {
        const val = parseInt(selScanType.value);
        if (val === 2 || val === 3) {
            rowExposureTime.style.display = "block";
        } else {
            rowExposureTime.style.display = "none";
        }
    });

    btnReconnect.addEventListener("click", handleReconnect);
    btnSaveConfig.addEventListener("click", applyParameters);
    btnScan.addEventListener("click", executeScan);
    btnSecure.addEventListener("click", triggerSecureStandby);
    btnExportCsv.addEventListener("click", exportToCSV);
    
    chkLamp.addEventListener("change", toggleLamp);
    chkHibernate.addEventListener("change", toggleHibernate);
    
    chkWatchdog.addEventListener("change", updateWatchdogConfig);
    rngTimeout.addEventListener("input", () => {
        lblTimeout.textContent = `${rngTimeout.value}s`;
    });
    rngTimeout.addEventListener("change", updateWatchdogConfig);
    
    rngWarmup.addEventListener("input", () => {
        lblWarmup.textContent = `${parseFloat(rngWarmup.value).toFixed(1)}s`;
    });
    
    chkAutoLamp.addEventListener("change", () => {
        if (chkAutoLamp.checked) {
            warmupSettingGroup.className = "form-row warmup-row mb-4";
        } else {
            warmupSettingGroup.className = "form-row warmup-row mb-4 hidden";
        }
    });
    
    // Tab controls
    tabReflectance.addEventListener("click", () => {
        tabReflectance.classList.add("active");
        tabReconstructed.classList.remove("active");
        activeTab = "reflectance";
        updateChart();
    });
    
    tabReconstructed.addEventListener("click", () => {
        tabReconstructed.classList.add("active");
        tabReflectance.classList.remove("active");
        activeTab = "reconstructed";
        updateChart();
    });
    
    btnClearLogs.addEventListener("click", () => {
        logTerminal.innerHTML = "";
        log("Logs cleared.", "info");
    });

    // Start App Initialization
    initChart();
    handleReconnect(); // Auto connect on startup
    
    // Periodically poll status every 4s
    setInterval(checkStatus, 4000);
});
