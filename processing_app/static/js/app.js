// DLP NIRscan Nano - Spectral Processing Studio JavaScript Logic
document.addEventListener("DOMContentLoaded", () => {
    
    // UI Elements Selection
    const btnRefreshFiles = document.getElementById("btn-refresh-files");
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const filesList = document.getElementById("files-list");
    
    const chkBaseOffset = document.getElementById("chk-base-offset");
    const chkBaseSnv = document.getElementById("chk-base-snv");
    const chkBaseMinmax = document.getElementById("chk-base-minmax");
    const btnSavePlotPng = document.getElementById("btn-save-plot-png");
    const btnExportProcessedCsv = document.getElementById("btn-export-processed-csv");
    
    const selSmoothing = document.getElementById("sel-smoothing");
    const savgolSettings = document.getElementById("savgol-settings");
    const sgWindow = document.getElementById("sg-window");
    const sgPoly = document.getElementById("sg-poly");
    const movingAvgSettings = document.getElementById("moving-avg-settings");
    const maWindow = document.getElementById("ma-window");
    
    const chkStackMode = document.getElementById("chk-stack-mode");
    const stackOffsetContainer = document.getElementById("stack-offset-container");
    const rngStackOffset = document.getElementById("rng-stack-offset");
    const lblStackOffset = document.getElementById("lbl-stack-offset");
    const lblChartMode = document.getElementById("lbl-chart-mode");
    
    const selPeakType = document.getElementById("sel-peak-type");
    const rngThreshold = document.getElementById("rng-threshold");
    const lblThreshold = document.getElementById("lbl-threshold");
    
    const bandsTable = document.getElementById("bands-table").querySelector("tbody");

    // Local Variables
    let localFiles = [];
    let selectedFiles = [];
    let spectraChart = null;
    let processedSpectra = null;
    let fileRenames = {};
    
    // Distinct colors for rendering multiple spectra overlay
    const colors = [
        '#22d3ee', // Cyan
        '#818cf8', // Purple/Indigo
        '#10b981', // Emerald Green
        '#fbbf24', // Amber/Yellow
        '#f472b6', // Pink
        '#fb7185', // Rose
        '#38bdf8', // Sky Blue
        '#a78bfa', // Violet
        '#34d399', // Green
        '#f59e0b'  // Orange
    ];

    const customPeakLabelsPlugin = {
        id: 'customPeakLabels',
        afterDatasetsDraw(chart, args, options) {
            const { ctx } = chart;
            chart.data.datasets.forEach((dataset, datasetIndex) => {
                if (dataset.type === 'scatter') {
                    const meta = chart.getDatasetMeta(datasetIndex);
                    dataset.data.forEach((point, index) => {
                        const element = meta.data[index];
                        if (element && point.label) {
                            ctx.save();
                            ctx.font = 'bold 9px Plus Jakarta Sans, sans-serif';
                            ctx.textAlign = 'center';
                            
                            const text = point.label;
                            const textWidth = ctx.measureText(text).width;
                            const xVal = element.x;
                            const yVal = element.y - 12;
                            
                            const rectWidth = textWidth + 8;
                            const rectHeight = 14;
                            const rectX = xVal - rectWidth / 2;
                            const rectY = yVal - 10;
                            
                            ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
                            ctx.strokeStyle = '#334155';
                            ctx.lineWidth = 1;
                            
                            ctx.beginPath();
                            if (ctx.roundRect) {
                                ctx.roundRect(rectX, rectY, rectWidth, rectHeight, 3);
                            } else {
                                ctx.rect(rectX, rectY, rectWidth, rectHeight);
                            }
                            ctx.fill();
                            ctx.stroke();
                            
                            ctx.fillStyle = '#22d3ee';
                            ctx.fillText(text, xVal, yVal);
                            ctx.restore();
                        }
                    });
                }
            });
        }
    };

    // Initialize Chart.js
    function initChart() {
        const ctx = document.getElementById('spectrumChart').getContext('2d');
        
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
        
        spectraChart = new Chart(ctx, {
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
                            font: { size: 12, weight: '500' },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        usePointStyle: true
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Wavelength (nm)',
                            font: { size: 13, weight: '600' }
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.05)' }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Reflectance',
                            font: { size: 13, weight: '600' }
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.05)' }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            },
            plugins: [customPeakLabelsPlugin]
        });
    }

    // Refresh Local File List
    async function loadFiles() {
        try {
            const res = await fetch("/api/files");
            const data = await res.json();
            
            if (data.success) {
                localFiles = data.files;
                renderFileList();
            }
        } catch (err) {
            console.error("Error loading files list:", err);
        }
    }

    // Render local file checklists
    function renderFileList() {
        filesList.innerHTML = "";
        
        if (localFiles.length === 0) {
            filesList.innerHTML = `<div class="no-files-notice">No spectra files detected. Scan some samples or upload files.</div>`;
            return;
        }
        
        localFiles.forEach(file => {
            const item = document.createElement("div");
            item.className = "file-item";
            
            // Checkbox
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.value = file.name;
            checkbox.id = `chk-file-${file.name}`;
            
            // Re-select if it was selected previously
            if (selectedFiles.some(f => f.name === file.name)) {
                checkbox.checked = true;
            }
            
            checkbox.addEventListener("change", () => {
                handleFileSelection(file, checkbox.checked);
            });
            
            const textGroup = document.createElement("div");
            textGroup.className = "file-item-text";
            
            const nameSpan = document.createElement("span");
            nameSpan.className = "file-name";
            nameSpan.textContent = fileRenames[file.name] || file.name;
            nameSpan.title = file.name;
            
            const metaGroup = document.createElement("div");
            metaGroup.className = "file-meta";
            
            const sourceBadge = document.createElement("span");
            sourceBadge.className = `file-source-badge source-${file.source}`;
            sourceBadge.textContent = file.source;
            
            metaGroup.appendChild(sourceBadge);
            
            textGroup.appendChild(nameSpan);
            textGroup.appendChild(metaGroup);
            
            // Edit button for renaming display label
            const editBtn = document.createElement("button");
            editBtn.className = "btn-edit-filename";
            editBtn.innerHTML = '<i class="fa-solid fa-pen-to-square"></i>';
            editBtn.title = "Rename Display Label";
            editBtn.addEventListener("click", (e) => {
                e.stopPropagation(); // prevent triggering check checkbox toggle
                const currentLabel = fileRenames[file.name] || file.name;
                const newLabel = prompt(`Enter a display name/label for: ${file.name}`, currentLabel);
                if (newLabel !== null) {
                    const cleanLabel = newLabel.trim();
                    if (cleanLabel !== "") {
                        fileRenames[file.name] = cleanLabel;
                    } else {
                        delete fileRenames[file.name];
                    }
                    renderFileList();
                    processSelectedSpectra(); // Refresh graph and legends
                }
            });
            
            item.appendChild(checkbox);
            item.appendChild(textGroup);
            item.appendChild(editBtn);
            
            // Clicking the item text checks the checkbox
            textGroup.addEventListener("click", () => {
                checkbox.checked = !checkbox.checked;
                handleFileSelection(file, checkbox.checked);
            });
            
            filesList.appendChild(item);
        });
    }

    // Update selection array and trigger recalculate
    function handleFileSelection(file, isChecked) {
        if (isChecked) {
            if (!selectedFiles.some(f => f.name === file.name)) {
                selectedFiles.push(file);
            }
        } else {
            selectedFiles = selectedFiles.filter(f => f.name !== file.name);
        }
        processSelectedSpectra();
    }

    // Drag and Drop File Upload
    dropZone.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            uploadFile(fileInput.files[0]);
        }
    });
    
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });
    
    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });
    
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    async function uploadFile(file) {
        if (!file.name.endsWith('.csv')) {
            alert("Only CSV files are supported.");
            return;
        }
        
        const formData = new FormData();
        formData.append("file", file);
        
        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                loadFiles();
            } else {
                alert(data.message);
            }
        } catch (err) {
            console.error("Upload failed:", err);
        }
    }

    // Call process API to process and load spectra
    async function processSelectedSpectra() {
        if (selectedFiles.length === 0) {
            processedSpectra = null;
            spectraChart.data.labels = [];
            spectraChart.data.datasets = [];
            spectraChart.update();
            renderBandsTable([]);
            return;
        }
        
        const baselines = [];
        if (chkBaseOffset.checked) baselines.push("offset");
        if (chkBaseSnv.checked) baselines.push("snv");
        if (chkBaseMinmax.checked) baselines.push("minmax");
        
        const smoothing = selSmoothing.value;
        const sg_window = parseInt(sgWindow.value);
        const sg_poly = parseInt(sgPoly.value);
        const ma_window = parseInt(maWindow.value);
        const peak_type = selPeakType.value;
        const threshold_factor = parseFloat(rngThreshold.value);
        
        const stack_mode = chkStackMode.checked;
        const stack_offset = parseFloat(rngStackOffset.value);
        
        try {
            const res = await fetch("/api/process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    files: selectedFiles,
                    baselines,
                    smoothing,
                    sg_window,
                    sg_poly,
                    ma_window,
                    peak_type,
                    threshold_factor,
                    stack_mode,
                    stack_offset
                })
            });
            const data = await res.json();
            
            if (data.success) {
                processedSpectra = data.spectra;
                updateChart();
            }
        } catch (err) {
            console.error("Error processing spectra:", err);
        }
    }

    // Update Chart with preprocessed spectra and peak scatter markers
    function updateChart() {
        if (!processedSpectra) return;
        
        spectraChart.data.datasets = [];
        let labelsExposed = false;
        let allPeaks = [];
        
        let datasetIdx = 0;
        
        for (const [filename, spectrum] of Object.entries(processedSpectra)) {
            const color = colors[datasetIdx % colors.length];
            datasetIdx++;
            
            // Populate X axis labels from first spectrum
            if (!labelsExposed) {
                spectraChart.data.labels = spectrum.wavelengths.map(w => w.toFixed(1));
                labelsExposed = true;
            }
            
            // Add preprocessed spectrum dataset line
            spectraChart.data.datasets.push({
                label: fileRenames[filename] || filename,
                data: spectrum.display_reflectance,
                borderColor: color,
                backgroundColor: color + '08', // subtle fill
                borderWidth: 2,
                tension: 0.15,
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: false,
                segment: {}
            });
            
            // Collect peak coordinates for scatter overlay
            spectrum.peaks.forEach(peak => {
                // Collect details
                allPeaks.push({
                    file: fileRenames[filename] || filename,
                    wavelength: peak.wavelength,
                    value: peak.value,
                    display_value: spectrum.display_reflectance[peak.index], // handles vertical offset shift in stack mode
                    molecule: peak.molecule,
                    assignment: peak.assignment,
                    color: color
                });
            });
        }
        
        // Add Peaks scatter overlay dataset
        if (allPeaks.length > 0) {
            const peakDataset = {
                label: selPeakType.value === 'peaks' ? 'Reflection Peaks' : 'Absorption Valleys',
                data: allPeaks.map(p => ({
                    x: p.wavelength.toFixed(1),
                    y: p.display_value,
                    label: `${p.wavelength.toFixed(0)}nm (${p.molecule})`
                })),
                type: 'scatter',
                borderColor: '#ef4444',
                backgroundColor: '#f87171',
                pointRadius: 6,
                pointHoverRadius: 9,
                pointStyle: selPeakType.value === 'peaks' ? 'triangle' : 'rectRot',
                borderWidth: 1.5,
                showLine: false,
                z: 100 // draw on top
            };
            spectraChart.data.datasets.push(peakDataset);
        }
        
        spectraChart.update();
        
        // Populate band assignments table
        renderBandsTable(allPeaks);
    }

    // Render detected peaks / band assignment table rows
    function renderBandsTable(peaks) {
        bandsTable.innerHTML = "";
        
        if (peaks.length === 0) {
            bandsTable.innerHTML = `
                <tr class="empty-row-placeholder">
                    <td colspan="5">Select spectra and enable band detection to view molecular assignments.</td>
                </tr>`;
            return;
        }
        
        peaks.forEach(peak => {
            const row = document.createElement("tr");
            row.id = `row-peak-${peak.file.replace(/[^a-zA-Z0-9]/g, '')}-${peak.wavelength.toFixed(1)}`;
            
            const cellFile = document.createElement("td");
            cellFile.textContent = peak.file;
            cellFile.className = "file-col";
            
            const cellWavelength = document.createElement("td");
            cellWavelength.textContent = `${peak.wavelength.toFixed(2)} nm`;
            
            const cellValue = document.createElement("td");
            cellValue.textContent = peak.value.toFixed(4);
            
            const cellMolecule = document.createElement("td");
            cellMolecule.textContent = peak.molecule;
            cellMolecule.style.color = "var(--accent-cyan)";
            cellMolecule.style.fontWeight = "600";
            
            const cellAssignment = document.createElement("td");
            cellAssignment.textContent = peak.assignment;
            
            row.appendChild(cellFile);
            row.appendChild(cellWavelength);
            row.appendChild(cellValue);
            row.appendChild(cellMolecule);
            row.appendChild(cellAssignment);
            
            // Hover table row to highlight peak on Chart
            row.addEventListener("mouseenter", () => {
                row.classList.add("highlighted");
                highlightPeakOnChart(peak, true);
            });
            row.addEventListener("mouseleave", () => {
                row.classList.remove("highlighted");
                highlightPeakOnChart(peak, false);
            });
            
            bandsTable.appendChild(row);
        });
    }

    // High-quality peak highlighting on Chart.js
    function highlightPeakOnChart(peak, highlight) {
        if (!spectraChart) return;
        
        // Find the scatter dataset index
        const datasetIdx = spectraChart.data.datasets.findIndex(d => d.type === 'scatter');
        if (datasetIdx === -1) return;
        
        const data = spectraChart.data.datasets[datasetIdx].data;
        const wlStr = peak.wavelength.toFixed(1);
        
        // Find index of matching point in dataset
        const ptIdx = data.findIndex(pt => pt.x === wlStr && Math.abs(pt.y - peak.display_value) < 1e-4);
        if (ptIdx === -1) return;
        
        // Set custom styling for just this point
        const meta = spectraChart.getDatasetMeta(datasetIdx);
        const element = meta.data[ptIdx];
        if (element) {
            if (highlight) {
                element.options.radius = 12;
                element.options.hoverRadius = 14;
                element.options.backgroundColor = '#22d3ee';
                element.options.borderColor = '#ffffff';
            } else {
                element.options.radius = 6;
                element.options.hoverRadius = 9;
                element.options.backgroundColor = '#f87171';
                element.options.borderColor = '#ef4444';
            }
            spectraChart.update('none'); // silent update without animation lag
        }
    }

    // Save current chart as scientific PNG with a solid background color
    function saveChartAsImage() {
        if (!spectraChart) return;
        
        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = spectraChart.width;
        tempCanvas.height = spectraChart.height;
        const tempCtx = tempCanvas.getContext("2d");
        
        // Draw solid background matching the premium dark obsidian dashboard card theme
        tempCtx.fillStyle = "#0b0f19";
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        // Draw Chart.js canvas elements
        tempCtx.drawImage(spectraChart.canvas, 0, 0);
        
        // Trigger download
        const link = document.createElement("a");
        const timestamp = new Date().toISOString().slice(0, 19).replace(/T|:/g, "_");
        link.download = `scientific_nir_plot_${timestamp}.png`;
        link.href = tempCanvas.toDataURL("image/png");
        link.click();
    }

    // Export processed spectra data as clean CSV for scientific tooling (Excel, Origin, MATLAB)
    function exportProcessedDataCSV() {
        if (!processedSpectra || Object.keys(processedSpectra).length === 0) {
            alert("No processed spectra data available to export.");
            return;
        }
        
        const firstFile = Object.keys(processedSpectra)[0];
        const wavelengths = processedSpectra[firstFile].wavelengths;
        const filenames = Object.keys(processedSpectra);
        
        let csvContent = "Wavelength (nm)";
        filenames.forEach(f => {
            const displayName = fileRenames[f] || f;
            csvContent += `,${displayName} (Original Reflectance),${displayName} (Processed Reflectance)`;
        });
        csvContent += "\n";
        
        for (let i = 0; i < wavelengths.length; i++) {
            let row = wavelengths[i].toFixed(2);
            filenames.forEach(f => {
                const orig = processedSpectra[f].original_reflectance[i];
                const proc = processedSpectra[f].processed_reflectance[i];
                row += `,${orig.toFixed(6)},${proc.toFixed(6)}`;
            });
            csvContent += row + "\n";
        }
        
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        const timestamp = new Date().toISOString().slice(0, 10);
        link.download = `processed_spectra_data_${timestamp}.csv`;
        link.href = URL.createObjectURL(blob);
        link.click();
    }

    // Preprocessing Event Listeners
    chkBaseOffset.addEventListener("change", processSelectedSpectra);
    chkBaseSnv.addEventListener("change", processSelectedSpectra);
    chkBaseMinmax.addEventListener("change", processSelectedSpectra);
    
    selSmoothing.addEventListener("change", () => {
        const val = selSmoothing.value;
        if (val === 'savgol') {
            savgolSettings.classList.remove("hidden");
            movingAvgSettings.classList.add("hidden");
        } else if (val === 'moving_avg') {
            movingAvgSettings.classList.remove("hidden");
            savgolSettings.classList.add("hidden");
        } else {
            savgolSettings.classList.add("hidden");
            movingAvgSettings.classList.add("hidden");
        }
        processSelectedSpectra();
    });
    
    sgWindow.addEventListener("change", processSelectedSpectra);
    sgPoly.addEventListener("change", processSelectedSpectra);
    maWindow.addEventListener("change", processSelectedSpectra);
    
    chkStackMode.addEventListener("change", () => {
        if (chkStackMode.checked) {
            stackOffsetContainer.classList.remove("hidden");
            lblChartMode.textContent = "Mode: Cascade Stack";
        } else {
            stackOffsetContainer.classList.add("hidden");
            lblChartMode.textContent = "Mode: Overlay";
        }
        processSelectedSpectra();
    });
    
    rngStackOffset.addEventListener("input", () => {
        lblStackOffset.textContent = rngStackOffset.value;
    });
    rngStackOffset.addEventListener("change", processSelectedSpectra);
    
    selPeakType.addEventListener("change", processSelectedSpectra);
    
    rngThreshold.addEventListener("input", () => {
        lblThreshold.textContent = parseFloat(rngThreshold.value).toFixed(2);
    });
    rngThreshold.addEventListener("change", processSelectedSpectra);
    
    btnRefreshFiles.addEventListener("click", () => {
        loadFiles();
    });

    btnSavePlotPng.addEventListener("click", saveChartAsImage);
    btnExportProcessedCsv.addEventListener("click", exportProcessedDataCSV);
 
    // Start App Initialization
    initChart();
    loadFiles();
});
