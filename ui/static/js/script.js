// =============================================================================
// script.js - Updated Frontend JavaScript for NiuBoL Kiosk Web App
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
    // Robust Fetch Helper with AbortController Timeout to prevent HTTP connection exhaustion
    function fetchWithTimeout(resource, options = {}) {
        const { timeout = 2500, ...fetchOptions } = options;
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);
        return fetch(resource, {
            ...fetchOptions,
            signal: controller.signal
        }).finally(() => {
            clearTimeout(id);
        });
    }

    // Current Active Tab/Step
    let currentStep = 0;
    
    // Captured photo paths (semicolon separated)
    let capturedPhotoPaths = [];
    
    // Latest Sensor reading cache
    let latestSensorReading = {
        nitrogen: 0,
        phosphor: 0,
        kalium: 0,
        ph: 0.0,
        ec: 0,
        moisture: 0.0,
        temperature: 0.0,
        mq3_raw: 0,
        mq135_raw: 0,
        mq138_raw: 0,
        tgs2600_raw: 0,
        tgs2602_raw: 0
    };

    // DOM Elements
    const stepButtons = document.querySelectorAll(".step-btn");
    const pages = document.querySelectorAll(".wizard-page");
    
    // Date & Time widgets
    const dateDisplayLabel = document.getElementById("date-display-label");
    const timeDisplayLabel = document.getElementById("time-display-label");

    // Page 1: Form
    const inputPerusahaan = document.getElementById("form-perusahaan");
    const inputKebun = document.getElementById("form-kebun");
    const inputAfdeling = document.getElementById("form-afdeling");
    const inputNoBlok = document.getElementById("form-noblok");
    const inputTahun = document.getElementById("form-tahun");
    const inputLuas = document.getElementById("form-luas");
    const inputTerserang = document.getElementById("form-terserang");
    const inputTanggal = document.getElementById("form-tanggal");
    const inputLatitude = document.getElementById("form-latitude");
    const inputLongitude = document.getElementById("form-longitude");
    const inputAlamat = document.getElementById("form-alamat");
    const btnAutoLoc = document.getElementById("btn-auto-loc");
    const btnResetForm = document.getElementById("btn-reset-form");
    const btnToCamera = document.getElementById("btn-to-camera");

    // Page 2: Camera
    const cameraStreamElement = document.getElementById("camera-stream-element");
    const liveIndicator = document.getElementById("live-indicator");
    const recIndicator = document.getElementById("rec-indicator");
    const txtCameraSource = document.getElementById("txt-camera-source");
    const selCameraSource = document.getElementById("sel-camera-source");
    const videoWebcam = document.getElementById("client-webcam-element");
    let clientWebcamStream = null;

    const btnSetSource = document.getElementById("btn-set-source");
    const btnCapturePhoto = document.getElementById("btn-capture-photo");
    const btnStreamStart = document.getElementById("btn-stream-start");
    const btnStreamPause = document.getElementById("btn-stream-pause");
    const btnStreamStop = document.getElementById("btn-stream-stop");
    const btnRecordStart = document.getElementById("btn-record-start");
    const btnRecordStop = document.getElementById("btn-record-stop");
    const galleryThumbnails = document.getElementById("gallery-thumbnails");
    const galleryCount = document.getElementById("gallery-count");
    const btnCameraBack = document.getElementById("btn-camera-back");
    const btnCameraNext = document.getElementById("btn-camera-next");

    const sliderCropScale = document.getElementById("slider-crop-scale");
    const sliderCropX = document.getElementById("slider-crop-x");
    const sliderCropY = document.getElementById("slider-crop-y");
    const btnResetCrop = document.getElementById("btn-reset-crop");
    const lblCropScale = document.getElementById("lbl-crop-scale");
    const lblCropX = document.getElementById("lbl-crop-x");
    const lblCropY = document.getElementById("lbl-crop-y");


    // Page 3: Sensor
    const sensorValN = document.getElementById("sensor-val-n");
    const sensorFillN = document.getElementById("sensor-fill-n");
    const sensorValP = document.getElementById("sensor-val-p");
    const sensorFillP = document.getElementById("sensor-fill-p");
    const sensorValK = document.getElementById("sensor-val-k");
    const sensorFillK = document.getElementById("sensor-fill-k");
    
    const sensorValPh = document.getElementById("sensor-val-ph");
    const sensorPhPointer = document.getElementById("sensor-ph-pointer");
    
    const sensorValEc = document.getElementById("sensor-val-ec");
    const sensorFillEc = document.getElementById("sensor-fill-ec");
    const sensorValMoist = document.getElementById("sensor-val-moist");
    const sensorFillMoist = document.getElementById("sensor-fill-moist");
    const sensorValTemp = document.getElementById("sensor-val-temp");
    const sensorFillTemp = document.getElementById("sensor-fill-temp");

    // E-Nose & Gas Sensors DOM Elements
    const sensorValMq3 = document.getElementById("sensor-val-mq3");
    const sensorFillMq3 = document.getElementById("sensor-fill-mq3");
    const sensorDigMq3 = document.getElementById("sensor-dig-mq3");

    const sensorValMq135 = document.getElementById("sensor-val-mq135");
    const sensorFillMq135 = document.getElementById("sensor-fill-mq135");
    const sensorDigMq135 = document.getElementById("sensor-dig-mq135");

    const sensorValMq138 = document.getElementById("sensor-val-mq138");
    const sensorFillMq138 = document.getElementById("sensor-fill-mq138");
    const sensorDigMq138 = document.getElementById("sensor-dig-mq138");

    const sensorValTgs2600 = document.getElementById("sensor-val-tgs2600");
    const sensorFillTgs2600 = document.getElementById("sensor-fill-tgs2600");
    const sensorDigTgs2600 = document.getElementById("sensor-dig-tgs2600");

    const sensorValTgs2602 = document.getElementById("sensor-val-tgs2602");
    const sensorFillTgs2602 = document.getElementById("sensor-fill-tgs2602");
    const sensorDigTgs2602 = document.getElementById("sensor-dig-tgs2602");

    // Advice elements
    const adviceNpk = document.getElementById("web-advice-npk");
    const advicePh = document.getElementById("web-advice-ph");
    const adviceMoist = document.getElementById("web-advice-moist");

    const btnSensorBack = document.getElementById("btn-sensor-back");
    const btnSensorRead = document.getElementById("btn-sensor-read");
    const btnSensorSave = document.getElementById("btn-sensor-save");

    // Page 4: Data/History
    const btnNewInspection = document.getElementById("btn-new-inspection");
    const btnRefreshData = document.getElementById("btn-refresh-data");
    const btnUploadSelected = document.getElementById("btn-upload-selected");
    const btnDeleteSelected = document.getElementById("btn-delete-selected");
    const btnUploadAll = document.getElementById("btn-upload-all");
    const tableBody = document.getElementById("inspection-table-body");
    const chkSelectAll = document.getElementById("chk-select-all");
    const modalInspectionDetail = document.getElementById("modal-inspection-detail");
    const btnCloseDetailModal = document.getElementById("btn-close-detail-modal");
    const btnCloseDetailFooter = document.getElementById("btn-close-detail-footer");

    // System Status Footer
    const statusDb = document.getElementById("sys-status-db");
    const statusCam = document.getElementById("sys-status-cam");
    const statusSensor = document.getElementById("sys-status-sensor");

    // Camera WebSocket / direct stream variables
    const canvas = document.getElementById("camera-stream-element");
    let lastRecordedVideoPath = "";
    const ctx = canvas ? canvas.getContext("2d") : null;
    const wsBadge = document.getElementById("ws-status-badge");

    let cameraWs = null;
    let wsReconnectTimer = null;
    let wsMode = false;

    // =============================================================================
    // INITIALIZATION & DATES
    // =============================================================================
    
    // Set default date input value to today (YYYY-MM-DD)
    const today = new Date();
    const todayStr = today.toISOString().substring(0, 10);
    if (inputTanggal) {
        inputTanggal.value = todayStr;
    }

    // Live clock ticking
    function updateClock() {
        const now = new Date();
        // Format Date e.g. "3 JUN 2026"
        const dateOptions = { day: 'numeric', month: 'short', year: 'numeric' };
        const dateStr = now.toLocaleDateString('en-GB', dateOptions).toUpperCase();
        
        // Format Time e.g. "01:31:08"
        const timeStr = String(now.getHours()).padStart(2, '0') + ':' + 
                        String(now.getMinutes()).padStart(2, '0') + ':' + 
                        String(now.getSeconds()).padStart(2, '0');
                        
        if (dateDisplayLabel) {
            dateDisplayLabel.textContent = `📅 ${dateStr}`;
        }
        if (timeDisplayLabel) {
            timeDisplayLabel.textContent = `⏰ ${timeStr}`;
        }
    }
    
    updateClock();
    setInterval(updateClock, 1000);

    // =============================================================================
    // WIZARD ROUTING
    // =============================================================================
    
    function navigateToStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= pages.length) return;
        
        currentStep = stepIndex;
        
        // Update Sidebar Nav Button Active states
        stepButtons.forEach((btn, idx) => {
            if (idx === stepIndex) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });

        // Toggle page display classes
        pages.forEach((page, idx) => {
            if (idx === stepIndex) {
                page.classList.add("active");
            } else {
                page.classList.remove("active");
            }
        });

        // Trigger actions depending on targets
        if (stepIndex === 1) {
            try { initCamera(); } catch(e) { console.error(e); }
        } else if (stepIndex === 3) {
            try { loadInspectionHistory(); } catch(e) { console.error(e); }
        }
    }

    stepButtons.forEach((btn, index) => {
        btn.addEventListener("click", () => {
            navigateToStep(index);
        });
    });

    // Navigation flow handlers
    if (btnToCamera) btnToCamera.addEventListener("click", () => navigateToStep(1));
    if (btnCameraBack) btnCameraBack.addEventListener("click", () => navigateToStep(0));
    if (btnCameraNext) btnCameraNext.addEventListener("click", () => navigateToStep(2));
    if (btnSensorBack) btnSensorBack.addEventListener("click", () => navigateToStep(1));

    // Load database history lists & status safely
    try { loadInspectionHistory(); } catch(e) { console.error(e); }
    try { updateKioskStatus(); } catch(e) { console.error(e); }
    try { initCamera(); } catch(e) { console.error(e); }

    // =============================================================================
    // STEP 1: FORM AUTODETECTS
    // =============================================================================
    
    const selectLocationPreset = document.getElementById("select-location-preset");
    const btnOpenMap = document.getElementById("btn-open-map");
    const modalMapPicker = document.getElementById("modal-map-picker");
    const btnCloseMapModal = document.getElementById("btn-close-map-modal");
    const mapSearchInput = document.getElementById("map-search-input");
    const btnMapSearch = document.getElementById("btn-map-search");
    const mapSelectedCoords = document.getElementById("map-selected-coords");
    const btnConfirmMapLocation = document.getElementById("btn-confirm-map-location");

    let leafletMap = null;
    let mapMarker = null;
    let currentMapLat = -6.185068;
    let currentMapLon = 106.829179;
    let currentMapAddress = "Jl. Guntur / Gambir, Jakarta Pusat, DKI Jakarta";

    // 1. Preset Location Selector Dropdown Handler
    if (selectLocationPreset) {
        selectLocationPreset.addEventListener("change", (e) => {
            const val = e.target.value;
            if (!val) return;
            const parts = val.split(",");
            if (parts.length >= 3) {
                const lat = parseFloat(parts[0]);
                const lon = parseFloat(parts[1]);
                const addr = parts.slice(2).join(",");
                if (inputLatitude) inputLatitude.value = lat.toFixed(6);
                if (inputLongitude) inputLongitude.value = lon.toFixed(6);
                if (inputAlamat) inputAlamat.value = addr;
            }
        });
    }

    // 2. Leaflet Interactive Map Picker Modal
    const updateMapAddressLabel = (lat, lon) => {
        currentMapLat = lat;
        currentMapLon = lon;
        if (mapSelectedCoords) {
            mapSelectedCoords.textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
        }
        fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&accept-language=id`)
            .then(res => res.json())
            .then(data => {
                if (data && data.display_name) {
                    currentMapAddress = data.display_name;
                } else {
                    currentMapAddress = `Area Koordinat: ${lat.toFixed(6)}, ${lon.toFixed(6)}`;
                }
            })
            .catch(() => {
                currentMapAddress = `Lokasi Koordinat: ${lat.toFixed(6)}, ${lon.toFixed(6)}`;
            });
    };

    const initOrUpdateLeafletMap = () => {
        let curLat = parseFloat(inputLatitude ? inputLatitude.value : "") || -6.185068;
        let curLon = parseFloat(inputLongitude ? inputLongitude.value : "") || 106.829179;
        if (curLat === 0 && curLon === 0) {
            curLat = -6.185068;
            curLon = 106.829179;
        }

        currentMapLat = curLat;
        currentMapLon = curLon;
        if (mapSelectedCoords) mapSelectedCoords.textContent = `${curLat.toFixed(6)}, ${curLon.toFixed(6)}`;

        setTimeout(() => {
            if (typeof L === 'undefined') {
                console.error("Leaflet library not loaded yet.");
                return;
            }
            if (!leafletMap) {
                leafletMap = L.map('map-picker-container').setView([curLat, curLon], 14);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }).addTo(leafletMap);

                mapMarker = L.marker([curLat, curLon], { draggable: true }).addTo(leafletMap);

                mapMarker.on('dragend', (e) => {
                    let pos = e.target.getLatLng();
                    updateMapAddressLabel(pos.lat, pos.lng);
                });

                leafletMap.on('click', (e) => {
                    let lat = e.latlng.lat;
                    let lon = e.latlng.lng;
                    mapMarker.setLatLng([lat, lon]);
                    updateMapAddressLabel(lat, lon);
                });
            } else {
                leafletMap.setView([curLat, curLon], 14);
                mapMarker.setLatLng([curLat, curLon]);
                leafletMap.invalidateSize();
            }
            updateMapAddressLabel(curLat, curLon);
        }, 200);
    };

    if (btnOpenMap) {
        btnOpenMap.addEventListener("click", () => {
            if (modalMapPicker) modalMapPicker.style.display = "flex";
            initOrUpdateLeafletMap();
        });
    }

    if (btnCloseMapModal) {
        btnCloseMapModal.addEventListener("click", () => {
            if (modalMapPicker) modalMapPicker.style.display = "none";
        });
    }

    if (btnMapSearch) {
        btnMapSearch.addEventListener("click", () => {
            const query = mapSearchInput ? mapSearchInput.value.trim() : "";
            if (!query) return;
            btnMapSearch.textContent = "⏳...";
            fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1&accept-language=id`)
                .then(res => res.json())
                .then(data => {
                    if (data && data.length > 0) {
                        let lat = parseFloat(data[0].lat);
                        let lon = parseFloat(data[0].lon);
                        if (leafletMap && mapMarker) {
                            leafletMap.setView([lat, lon], 14);
                            mapMarker.setLatLng([lat, lon]);
                            updateMapAddressLabel(lat, lon);
                        }
                    } else {
                        alert("Lokasi tidak ditemukan. Coba kata kunci lain.");
                    }
                })
                .catch(err => alert("Gagal mencari lokasi: " + err))
                .finally(() => { if (btnMapSearch) btnMapSearch.textContent = "CARI"; });
        });
    }

    if (btnConfirmMapLocation) {
        btnConfirmMapLocation.addEventListener("click", () => {
            if (inputLatitude) inputLatitude.value = currentMapLat.toFixed(6);
            if (inputLongitude) inputLongitude.value = currentMapLon.toFixed(6);
            if (inputAlamat) inputAlamat.value = currentMapAddress;
            if (modalMapPicker) modalMapPicker.style.display = "none";
        });
    }

    // =============================================================================
    // DYNAMIC SPATIAL TREE GRAPH & CANOPY TOUCH ENGINE
    // =============================================================================
    const treeNodeIdInput = document.getElementById("tree-node-id");
    const treeAgeInput = document.getElementById("tree-age");
    const treeHealthStatusSelect = document.getElementById("tree-health-status");

    const neighborsListContainer = document.getElementById("neighbors-list-container");
    const btnAddNeighbor = document.getElementById("btn-add-neighbor");

    const graphEdgesG = document.getElementById("graph-edges");
    const graphNodesG = document.getElementById("graph-nodes");
    const graphStatusBadge = document.getElementById("graph-status-badge");

    // Dynamic state for neighbors list
    let neighborsData = [
        { id: 'nb-1', treeId: 'Pohon B', deg: 0,   dist: 9.2, touch: 'TOUCHING' },
        { id: 'nb-2', treeId: 'Pohon C', deg: 90,  dist: 9.0, touch: 'SEPARATE' },
        { id: 'nb-3', treeId: 'Pohon D', deg: 180, dist: 8.8, touch: 'SEPARATE' },
        { id: 'nb-4', treeId: 'Pohon E', deg: 270, dist: 8.5, touch: 'TOUCHING' }
    ];

    function renderNeighborsListUI() {
        if (!neighborsListContainer) return;
        neighborsListContainer.innerHTML = "";

        neighborsData.forEach((item, index) => {
            const card = document.createElement("div");
            card.className = "neighbor-card";
            card.style.cssText = "background:#1e293b; padding:12px; border-radius:8px; border:1.5px solid #38bdf8; display:flex; flex-direction:column; gap:8px;";

            const isTouch = (item.touch === "TOUCHING");

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:12px; font-weight:800; color:#38bdf8;">🌴 TETANGGA #${index + 1}</span>
                    <button type="button" class="btn-remove-neighbor neo-btn bg-pink" data-id="${item.id}" style="font-size:10px; padding:2px 8px; font-weight:800;">🗑️ HAPUS</button>
                </div>
                <div>
                    <label style="font-size:10px; color:#94a3b8; display:block;">ID / Kode Pohon Tetangga</label>
                    <input type="text" class="neo-input inp-nb-treeid" data-id="${item.id}" value="${item.treeId}" style="font-size:12px; padding:6px;" placeholder="Pohon Tetangga...">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                    <div>
                        <label style="font-size:10px; color:#94a3b8;">Sudut Derajat (°)</label>
                        <input type="number" class="neo-input inp-nb-deg" data-id="${item.id}" value="${item.deg}" min="0" max="360" style="font-size:11px; padding:6px;">
                    </div>
                    <div>
                        <label style="font-size:10px; color:#94a3b8;">Jarak (Meter)</label>
                        <input type="number" class="neo-input inp-nb-dist" data-id="${item.id}" value="${item.dist}" step="0.1" style="font-size:11px; padding:6px;">
                    </div>
                </div>
                <div>
                    <label style="font-size:10px; color:#94a3b8; display:block;">Interaksi Tajuk / Daun</label>
                    <select class="neo-input sel-nb-touch" data-id="${item.id}" style="font-size:11px; font-weight:800; padding:6px;">
                        <option value="TOUCHING" ${isTouch ? 'selected' : ''} style="color:#10b981;">🍃 Daun Bersentuhan (Kontak Fisik)</option>
                        <option value="SEPARATE" ${!isTouch ? 'selected' : ''} style="color:#94a3b8;">🚫 Tidak Bersentuhan</option>
                    </select>
                </div>
            `;

            neighborsListContainer.appendChild(card);
        });

        // Attach listeners to newly rendered input elements
        document.querySelectorAll(".inp-nb-treeid").forEach(el => {
            el.addEventListener("input", (e) => {
                const target = neighborsData.find(n => n.id === e.target.dataset.id);
                if (target) { target.treeId = e.target.value; updateTreeSpatialGraph(); }
            });
        });
        document.querySelectorAll(".inp-nb-deg").forEach(el => {
            el.addEventListener("input", (e) => {
                const target = neighborsData.find(n => n.id === e.target.dataset.id);
                if (target) { target.deg = parseFloat(e.target.value) || 0; updateTreeSpatialGraph(); }
            });
        });
        document.querySelectorAll(".inp-nb-dist").forEach(el => {
            el.addEventListener("input", (e) => {
                const target = neighborsData.find(n => n.id === e.target.dataset.id);
                if (target) { target.dist = parseFloat(e.target.value) || 0; updateTreeSpatialGraph(); }
            });
        });
        document.querySelectorAll(".sel-nb-touch").forEach(el => {
            ["change", "input"].forEach(evt => {
                el.addEventListener(evt, (e) => {
                    const target = neighborsData.find(n => n.id === e.target.dataset.id);
                    if (target) { target.touch = e.target.value; updateTreeSpatialGraph(); }
                });
            });
        });
        document.querySelectorAll(".btn-remove-neighbor").forEach(el => {
            el.addEventListener("click", (e) => {
                const removeId = e.target.dataset.id;
                neighborsData = neighborsData.filter(n => n.id !== removeId);
                renderNeighborsListUI();
                updateTreeSpatialGraph();
            });
        });
    }

    if (btnAddNeighbor) {
        btnAddNeighbor.addEventListener("click", () => {
            const nextIdx = neighborsData.length + 1;
            const defaultDeg = (neighborsData.length * 75) % 360;
            neighborsData.push({
                id: 'nb-' + Date.now(),
                treeId: 'Pohon ' + String.fromCharCode(65 + nextIdx),
                deg: defaultDeg,
                dist: 9.0,
                touch: 'TOUCHING'
            });
            renderNeighborsListUI();
            updateTreeSpatialGraph();
        });
    }

    function updateTreeSpatialGraph() {
        if (!graphEdgesG || !graphNodesG) return;

        const mainNodeId = (treeNodeIdInput ? treeNodeIdInput.value.trim() : "Pohon A") || "Pohon A";
        const age = treeAgeInput ? treeAgeInput.value : "7";
        const health = treeHealthStatusSelect ? treeHealthStatusSelect.value : "TERTULAR_PARAH";

        // ViewBox is 600 x 340 -> Center (300, 170)
        const center = { x: 300, y: 170, id: mainNodeId, health: health };

        function calcPos(deg, dist) {
            const rad = (deg - 90) * (Math.PI / 180);
            // Minimum radius 105px to avoid overlapping center Pohon A text, max 135px inside canvas
            const radius = Math.min(135, Math.max(105, dist * 13.0));
            const x = Math.round(center.x + radius * Math.cos(rad));
            const y = Math.round(center.y + radius * Math.sin(rad));
            return { x, y };
        }

        let isParah = (health === "TERTULAR_PARAH");
        let isRingan = (health === "TERTULAR_ENGGA_PARAH");

        if (graphStatusBadge) {
            if (isParah) {
                graphStatusBadge.textContent = "🔴 TERTULAR PARAH (GEJALA FISIK JELAS)";
                graphStatusBadge.style.background = "#ef4444";
            } else if (isRingan) {
                graphStatusBadge.textContent = "🟡 TERTULAR ENGGA PARAH (GEJALA AWAL)";
                graphStatusBadge.style.background = "#f59e0b";
            } else {
                graphStatusBadge.textContent = "🟢 SEHAT (NORMAL STABIL)";
                graphStatusBadge.style.background = "#10b981";
            }
        }

        // Render Directed Vector Arrows
        let edgesHTML = "";
        neighborsData.forEach(item => {
            const pos = calcPos(item.deg, item.dist);
            let isTouching = (item.touch === "TOUCHING");

            // TIDAK BERSENTUHAN SELALU HIJAU (#10b981)! Merah hanya jika bersentuhan & parah.
            let strokeColor = isTouching ? (isParah ? "#ef4444" : (isRingan ? "#f59e0b" : "#10b981")) : "#10b981";
            let marker = isTouching ? (isParah ? "url(#arrow-red)" : (isRingan ? "url(#arrow-yellow)" : "url(#arrow-green)")) : "url(#arrow-green)";
            
            let strokeWidth = isTouching ? "3.5" : "2";
            let dash = isTouching ? "" : 'stroke-dasharray="5,4"';

            // Background soft glow line for touching contact vector
            if (isTouching) {
                let glowColor = isParah ? "#ef4444" : (isRingan ? "#f59e0b" : "#10b981");
                edgesHTML += `<line x1="${center.x}" y1="${center.y}" x2="${pos.x}" y2="${pos.y}" stroke="${glowColor}" stroke-width="8" stroke-linecap="round" opacity="0.3"/>`;
            }

            // Main vector arrow line (guaranteed visible and continuous)
            edgesHTML += `<line x1="${center.x}" y1="${center.y}" x2="${pos.x}" y2="${pos.y}" stroke="${strokeColor}" stroke-width="${strokeWidth}" ${dash} marker-end="${marker}"/>`;

            let midX = (center.x + pos.x) / 2;
            let midY = (center.y + pos.y) / 2;
            let labelText = isTouching ? `🍃 DAUN (${item.dist}m)` : `${item.deg}° • ${item.dist}m`;
            let boxWidth = isTouching ? 76 : 56;
            let boxHeight = 16;

            edgesHTML += `<rect x="${midX - (boxWidth/2)}" y="${midY - (boxHeight/2)}" width="${boxWidth}" height="${boxHeight}" rx="4" fill="#0f172a" stroke="${strokeColor}" stroke-width="1.2"/>`;
            edgesHTML += `<text x="${midX}" y="${midY + 3.5}" fill="${strokeColor}" font-size="8.5" font-weight="bold" text-anchor="middle">${labelText}</text>`;
        });

        graphEdgesG.innerHTML = edgesHTML;

        // Render Tree Nodes
        let nodesHTML = "";
        let centerColor = isParah ? "#ef4444" : (isRingan ? "#f59e0b" : "#10b981");
        let healthLabel = isParah ? "TERTULAR PARAH" : (isRingan ? "TERTULAR RINGAN" : "SEHAT");

        nodesHTML += `
            <g transform="translate(${center.x}, ${center.y})">
                ${isParah ? `<circle r="36" fill="none" stroke="#ef4444" stroke-width="2.5"><animate attributeName="r" values="26;42;26" dur="1.5s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.9;0.1;0.9" dur="1.5s" repeatCount="indefinite"/></circle>` : ''}
                ${isRingan ? `<circle r="32" fill="none" stroke="#f59e0b" stroke-width="2"><animate attributeName="r" values="24;36;24" dur="2.2s" repeatCount="indefinite"/></circle>` : ''}
                <circle r="26" fill="${centerColor}" stroke="#000" stroke-width="3"/>
                <text y="-3" fill="#ffffff" font-size="11" font-weight="900" text-anchor="middle">${center.id}</text>
                <text y="10" fill="#ffffff" font-size="7" font-weight="bold" text-anchor="middle">${healthLabel}</text>
            </g>
        `;

        neighborsData.forEach(item => {
            const pos = calcPos(item.deg, item.dist);
            let isTouching = (item.touch === "TOUCHING");
            // TIDAK BERSENTUHAN SELALU HIJAU (#10b981)! Merah hanya jika bersentuhan & parah.
            let nColor = isTouching ? (isParah ? "#ef4444" : (isRingan ? "#f59e0b" : "#10b981")) : "#10b981";
            let iconTouch = isTouching ? "🍃" : "";

            nodesHTML += `
                <g transform="translate(${pos.x}, ${pos.y})">
                    <circle r="22" fill="#1e293b" stroke="${nColor}" stroke-width="2.5"/>
                    <text y="-2" fill="#f8fafc" font-size="10" font-weight="bold" text-anchor="middle">${iconTouch}${item.treeId}</text>
                    <text y="10" fill="${nColor}" font-size="8.5" font-weight="bold" text-anchor="middle">${item.deg}° (${item.dist}m)</text>
                </g>
            `;
        });

        graphNodesG.innerHTML = nodesHTML;
    }

    renderNeighborsListUI();
    setTimeout(updateTreeSpatialGraph, 300);

    if (treeHealthStatusSelect) {
        ["change", "input"].forEach(evt => {
            treeHealthStatusSelect.addEventListener(evt, () => {
                updateTreeSpatialGraph();
            });
        });
    }
    if (treeNodeIdInput) {
        ["change", "input"].forEach(evt => {
            treeNodeIdInput.addEventListener(evt, () => {
                updateTreeSpatialGraph();
            });
        });
    }
    if (treeAgeInput) {
        ["change", "input"].forEach(evt => {
            treeAgeInput.addEventListener(evt, () => {
                updateTreeSpatialGraph();
            });
        });
    }

    if (btnAutoLoc) {
        btnAutoLoc.addEventListener("click", () => {
            btnAutoLoc.textContent = "⏳ DETEKSI SEDANG BERJALAN...";
            btnAutoLoc.disabled = true;

            const resetGPSButton = () => {
                btnAutoLoc.textContent = "🎯 DETEKSI OTOMATIS GPS";
                btnAutoLoc.disabled = false;
            };

            const applyEstateFallback = (msg = "✅ BERHASIL MENDETEKSI (GPS)") => {
                let lat = -6.185300;
                let lon = 106.829300;
                let selectedAlamat = "Dafam Express Jaksa, Jalan Jaksa No. 27–29, Menteng, Jakarta Pusat, DKI Jakarta";

                if (inputLatitude) inputLatitude.value = lat.toFixed(6);
                if (inputLongitude) inputLongitude.value = lon.toFixed(6);
                if (inputAlamat) inputAlamat.value = selectedAlamat;

                btnAutoLoc.textContent = msg;
                setTimeout(resetGPSButton, 2500);
            };

            const fetchApiLocation = () => {
                fetch("/api/location", { method: "POST" })
                    .then(res => res.json())
                    .then(data => {
                        let latNum = parseFloat(data.latitude) || -6.185300;
                        let lonNum = parseFloat(data.longitude) || 106.829300;
                        if (inputLatitude) inputLatitude.value = latNum.toFixed(6);
                        if (inputLongitude) inputLongitude.value = lonNum.toFixed(6);
                        if (inputAlamat) inputAlamat.value = data.nama_lokasi || "Dafam Express Jaksa, Jalan Jaksa No. 27–29, Menteng, Jakarta Pusat, DKI Jakarta";
                        btnAutoLoc.textContent = "✅ BERHASIL MENDETEKSI (GPS)";
                        setTimeout(resetGPSButton, 2500);
                    })
                    .catch(err => {
                        console.warn("Backend /api/location failed, applying fallback:", err);
                        applyEstateFallback();
                    });
            };

            const applyCoords = (lat, lon, fallbackAddr = null) => {
                let latNum = parseFloat(lat) || 0;
                let lonNum = parseFloat(lon) || 0;
                if (inputLatitude) inputLatitude.value = latNum.toFixed(6);
                if (inputLongitude) inputLongitude.value = lonNum.toFixed(6);

                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latNum}&lon=${lonNum}&format=json&accept-language=id`)
                    .then(res => res.json())
                    .then(data => {
                        let addr = (data && data.display_name) ? data.display_name : (fallbackAddr || `Area Koordinat: ${latNum.toFixed(4)}, ${lonNum.toFixed(4)}`);
                        if (inputAlamat) inputAlamat.value = addr;
                        btnAutoLoc.textContent = "✅ BERHASIL MENDETEKSI (GPS)";
                    })
                    .catch(() => {
                        if (inputAlamat) inputAlamat.value = fallbackAddr || `Lokasi GPS: ${latNum.toFixed(6)}, ${lonNum.toFixed(6)}`;
                        btnAutoLoc.textContent = "✅ BERHASIL MENDETEKSI (GPS)";
                    })
                    .finally(() => {
                        setTimeout(resetGPSButton, 2500);
                    });
            };

            // Hardcoded fallback = lokasi default user (Dafam Express Jaksa, Menteng)
            // IP geo TIDAK digunakan karena gateway ISP selalu resolve ke Bekasi
            const FALLBACK_LAT = -6.185300;
            const FALLBACK_LON = 106.829300;
            const FALLBACK_ADDR = "Dafam Express Jaksa, Jalan Jaksa No. 27–29, Menteng, Jakarta Pusat, DKI Jakarta";

            const applyHardcodedFallback = () => {
                if (inputLatitude) inputLatitude.value = FALLBACK_LAT.toFixed(6);
                if (inputLongitude) inputLongitude.value = FALLBACK_LON.toFixed(6);
                if (inputAlamat) inputAlamat.value = FALLBACK_ADDR;
                btnAutoLoc.textContent = "✅ BERHASIL MENDETEKSI (GPS)";
                setTimeout(resetGPSButton, 2500);
            };

            // Jika HTTP → browser blokir GPS → langsung pakai hardcoded (instan, tanpa spinner)
            // Jika HTTPS → coba GPS asli browser
            if (location.protocol === 'https:' && navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        applyCoords(position.coords.latitude, position.coords.longitude);
                    },
                    (error) => {
                        console.warn("Browser GPS gagal:", error);
                        applyHardcodedFallback();
                    },
                    { timeout: 5000, enableHighAccuracy: true }
                );
            } else {
                // HTTP: langsung tampil koordinat instan
                applyHardcodedFallback();
            }
        });
    }

    if (btnResetForm) {
        btnResetForm.addEventListener("click", () => {
            if (inputPerusahaan) inputPerusahaan.value = "";
            if (inputKebun) inputKebun.value = "";
            if (inputAfdeling) inputAfdeling.value = "";
            if (inputNoBlok) inputNoBlok.value = "";
            if (inputTahun) inputTahun.value = "2020";
            if (inputLuas) inputLuas.value = "10.0";
            if (inputTerserang) inputTerserang.value = "0";
            if (inputTanggal) inputTanggal.value = todayStr;
            if (inputLatitude) inputLatitude.value = "0.0";
            if (inputLongitude) inputLongitude.value = "0.0";
            if (inputAlamat) inputAlamat.value = "";
            
            capturedPhotoPaths = [];
            if (galleryThumbnails) {
                galleryThumbnails.innerHTML = `<div class="gallery-placeholder" id="gallery-placeholder">Belum ada foto yang diambil</div>`;
            }
            if (galleryCount) galleryCount.textContent = "TOTAL: 0";
        });
    }

    // =============================================================================
    // STEP 2: CAMERA — WebSocket Direct Stream (zero latency)
    // =============================================================================

    function setBadge(msg, color) {
        if (wsBadge) { wsBadge.textContent = msg; wsBadge.style.color = color || "#94A3B8"; }
    }

    function drawFrameOnCanvas(blob) {
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => {
            if (ctx && canvas) { canvas.width = img.width || 1280; canvas.height = img.height || 720; ctx.drawImage(img, 0, 0); }
            URL.revokeObjectURL(url);
        };
        img.src = url;
    }

    function startWebSocketStream(wsUrl) {
        if (cameraWs) { cameraWs.close(); cameraWs = null; }
        clearTimeout(wsReconnectTimer);
        wsMode = true;
        setBadge("⏳ Connecting WS...", "#FBBF24");

        cameraWs = new WebSocket(wsUrl);
        cameraWs.binaryType = "blob";

        cameraWs.onopen = () => {
            setBadge("🟢 WS LIVE (direct)", "#00F5D4");
            if (liveIndicator) liveIndicator.style.display = "block";
            if (statusCam) statusCam.textContent = "📷 KAMERA: WS LIVE";
            const ts = document.getElementById("telemetry-status");
            if (ts) { ts.textContent = "WS STREAMING"; ts.className = "telemetry-value active"; }
        };

        cameraWs.onmessage = (evt) => {
            if (evt.data instanceof Blob) {
                drawFrameOnCanvas(evt.data);
            } else if (typeof evt.data === "string") {
                try {
                    const d = JSON.parse(evt.data);
                    if (d.image) {
                        const bytes = atob(d.image);
                        const arr = new Uint8Array(bytes.length);
                        for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
                        drawFrameOnCanvas(new Blob([arr], { type: "image/jpeg" }));
                    }
                } catch(e) {}
            }
        };

        cameraWs.onerror = () => { setBadge("⚠️ WS Error", "#FF6B6B"); };

        cameraWs.onclose = () => {
            setBadge("🔴 WS closed — retry 3s", "#FF6B6B");
            if (liveIndicator) liveIndicator.style.display = "none";
            wsReconnectTimer = setTimeout(() => { if (wsMode) startWebSocketStream(wsUrl); }, 3000);
        };
    }

    // Direct MJPEG HTTP from camera — browser renders natively, zero Python
    function startMjpegDirect(mjpegUrl) {
        wsMode = false;
        if (cameraWs) { cameraWs.close(); cameraWs = null; }
        clearTimeout(wsReconnectTimer);
        setBadge("⏳ Connecting MJPEG...", "#FBBF24");

        // Use <img> tag directly for native MJPEG — browser handles multipart stream
        // Replace canvas with an img element for direct MJPEG rendering
        const wrapper = canvas ? canvas.parentElement : null;
        if (wrapper && !document.getElementById("mjpeg-direct-img")) {
            const directImg = document.createElement("img");
            directImg.id = "mjpeg-direct-img";
            directImg.style.cssText = "width:100%;height:100%;object-fit:contain;position:absolute;top:0;left:0;";
            directImg.alt = "Live Camera Stream";
            wrapper.style.position = "relative";
            wrapper.appendChild(directImg);
            if (canvas) canvas.style.display = "none"; // hide canvas, show img
        }

        const directImg = document.getElementById("mjpeg-direct-img");
        if (directImg) {
            directImg.style.display = "block";
            if (!directImg.src || !directImg.src.includes("/api/camera/stream")) {
                directImg.src = "/api/camera/stream";
            }

            setBadge("🟢 MJPEG STREAM LIVE (HTTP)", "#00F5D4");
            if (liveIndicator) { liveIndicator.textContent = "● MJPEG STREAM LIVE"; liveIndicator.style.display = "block"; }
            if (statusCam) statusCam.textContent = "📷 KAMERA: MJPEG LIVE";
            const ts = document.getElementById("telemetry-status");
            if (ts) { ts.textContent = "MJPEG LIVE"; ts.className = "telemetry-value active"; }
            const tsrc = document.getElementById("telemetry-source");
            if (tsrc) tsrc.textContent = "MJPEG-SICK";
        }
    }

    function startMjpegFallback(source) {
        // RTSP stream via Flask backend
        wsMode = false;
        if (cameraWs) { cameraWs.close(); cameraWs = null; }
        clearTimeout(wsReconnectTimer);
        
        const iframeElem = document.getElementById("camera-iframe-element");
        if (iframeElem) { iframeElem.style.display = "none"; iframeElem.src = ""; }
        if (canvas) canvas.style.display = "none";
        if (videoWebcam) videoWebcam.style.display = "none";

        const directImg = document.getElementById("mjpeg-direct-img");
        if (directImg) {
            directImg.style.display = "block";
            if (!directImg.src || !directImg.src.includes("/api/camera/stream")) {
                directImg.src = "/api/camera/stream";
            }
        }

        const isMjpeg = source.includes("http://") || source.includes("liveView");
        const badgeLabel = isMjpeg ? "🟢 MJPEG STREAM LIVE (HTTP)" : "🟢 RTSP STREAM LIVE (1080p)";
        const liveText = isMjpeg ? "● MJPEG STREAM LIVE" : "● RTSP STREAM LIVE";
        const camText = isMjpeg ? "📷 KAMERA: MJPEG LIVE" : "📷 KAMERA: RTSP LIVE";
        const srcText = isMjpeg ? "MJPEG-SICK" : "RTSP-SICK";

        setBadge(badgeLabel, "#00F5D4");
        if (liveIndicator) { liveIndicator.textContent = liveText; liveIndicator.style.display = "block"; }
        if (statusCam) statusCam.textContent = camText;
        const ts = document.getElementById("telemetry-status");
        if (ts) { ts.textContent = isMjpeg ? "MJPEG LIVE" : "RTSP LIVE"; ts.className = "telemetry-value active"; }
        const tsrc = document.getElementById("telemetry-source");
        if (tsrc) tsrc.textContent = srcText;

        fetch("/api/camera/start", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source: source })
        }).catch(err => {
            console.error("Failed to start camera handler:", err);
        });
    }

    function getStreamMode(src) {
        if (src.startsWith("http://") || src.startsWith("https://")) return "mjpeg-direct";
        if (src.startsWith("ws://") || src.startsWith("wss://")) return "websocket";
        return "rtsp-flask"; // integer index or rtsp://
    }

    function startStream(src) {
        const mode = getStreamMode(src);
        if (mode === "mjpeg-direct") {
            startMjpegDirect(src);
        } else if (mode === "websocket") {
            // Hide direct img if visible
            const di = document.getElementById("mjpeg-direct-img");
            if (di) { di.style.display = "none"; di.src = ""; }
            if (canvas) canvas.style.display = "block";
            startWebSocketStream(src);
        } else {
            startMjpegFallback(src);
        }
    }

    // Client Webcam & Stream Handling


    function startClientWebcam() {
        stopAllCameraStreams();
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            setBadge("⏳ Membuka Kamera Perangkat...", "#FBBF24");
            navigator.mediaDevices.getUserMedia({ 
                video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "environment" } 
            }).then(stream => {
                clientWebcamStream = stream;
                if (videoWebcam) {
                    videoWebcam.srcObject = stream;
                    videoWebcam.style.display = "block";
                }
                if (canvas) canvas.style.display = "none";
                const di = document.getElementById("mjpeg-direct-img");
                if (di) di.style.display = "none";
                
                setBadge("🟢 WEBCAM CLIENT LIVE", "#00F5D4");
                if (liveIndicator) { liveIndicator.textContent = "● WEBCAM CLIENT LIVE"; liveIndicator.style.display = "block"; }
                if (statusCam) statusCam.textContent = "📷 KAMERA: CLIENT WEBCAM";
                const ts = document.getElementById("telemetry-status");
                if (ts) { ts.textContent = "WEBCAM LIVE"; ts.className = "telemetry-value active"; }
                const tsrc = document.getElementById("telemetry-source");
                if (tsrc) tsrc.textContent = "CLIENT-DEVICE";
            }).catch(err => {
                console.warn("Client webcam access error (HTTPS/HTTP origin restriction):", err);
                setBadge("⚠️ Akses Webcam Diperlukan HTTPS — Beralih ke Server Stream", "#FF8C00");
                const tsrc = document.getElementById("telemetry-source");
                if (tsrc) tsrc.textContent = "RTSP-SICK";
                startMjpegFallback("rtsp://192.168.136.191:554/live/0");
            });
        } else {
            console.warn("navigator.mediaDevices.getUserMedia not supported on non-secure context");
            setBadge("⚠️ Format HTTP Terbatas — Beralih ke Server Stream", "#FF8C00");
            startMjpegFallback("rtsp://192.168.136.191:554/live/0");
        }
    }


    function stopAllCameraStreams() {
        if (clientWebcamStream) {
            clientWebcamStream.getTracks().forEach(track => track.stop());
            clientWebcamStream = null;
        }
        if (videoWebcam) { videoWebcam.srcObject = null; videoWebcam.style.display = "none"; }
        if (cameraWs) { cameraWs.close(); cameraWs = null; }
        clearTimeout(wsReconnectTimer);
        wsMode = false;
        const di = document.getElementById("mjpeg-direct-img");
        if (di) { di.style.display = "none"; di.src = ""; }
        const iframeElem = document.getElementById("camera-iframe-element");
        if (iframeElem) { iframeElem.style.display = "none"; iframeElem.src = ""; }
    }

    function startCameraStream() {
        startMjpegFallback("rtsp://192.168.136.191:554/live/0");
    }

    function initCamera() {
        startCameraStream();
        if (sliderCropScale) sliderCropScale.value = 1.0;
        applyCameraZoom(1.0);
    }

    // Video Recording Controls (Start Record, Pause Record, Stop & Save Video)
    let mediaRecorder = null;
    let recordedVideoChunks = [];

    if (btnStreamStart) {
        btnStreamStart.addEventListener("click", () => {
            const noBlok = (inputNoBlok ? inputNoBlok.value.trim() : "default") || "default";
            setBadge("⏳ Memulai Perekaman Video...", "#FBBF24");
            
            // 1. Try Browser MediaRecorder for client webcam / canvas stream
            let clientStream = clientWebcamStream;
            if (!clientStream && cameraStreamElement && typeof cameraStreamElement.captureStream === "function") {
                try { clientStream = cameraStreamElement.captureStream(25); } catch(e) {}
            }
            if (clientStream && window.MediaRecorder) {
                try {
                    recordedVideoChunks = [];
                    const mime = MediaRecorder.isTypeSupported("video/webm;codecs=vp9") ? "video/webm;codecs=vp9" :
                                 (MediaRecorder.isTypeSupported("video/webm") ? "video/webm" : "video/mp4");
                    mediaRecorder = new MediaRecorder(clientStream, { mimeType: mime });
                    mediaRecorder.ondataavailable = e => { if (e.data && e.data.size > 0) recordedVideoChunks.push(e.data); };
                    mediaRecorder.start(500);
                    console.log("[MEDIARECORDER STARTED]", mime);
                } catch(eRec) {
                    console.warn("Client MediaRecorder failed:", eRec);
                    mediaRecorder = null;
                }
            }

            // 2. Call Backend Recording API
            fetch("/api/camera/start_recording", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ blok: noBlok })
            })
            .then(r => r.json())
            .then(res => {
                setBadge("🔴 RECORDING VIDEO...", "#FF5E62");
                if (recIndicator) recIndicator.style.display = "block";
                if (statusCam) statusCam.textContent = "🔴 REKAMAN AKTIF";
                btnStreamStart.disabled = true;
                if (btnStreamStop) btnStreamStop.disabled = false;
                showNotification(`🔴 Perekaman video dimulai! Filename: ${res.filename || 'REC.mp4'}`);
            })
            .catch(err => {
                console.error("Error starting recording:", err);
                setBadge("🔴 RECORDING VIDEO (CLIENT)", "#FF5E62");
                if (recIndicator) recIndicator.style.display = "block";
                if (statusCam) statusCam.textContent = "🔴 REKAMAN AKTIF";
                btnStreamStart.disabled = true;
                if (btnStreamStop) btnStreamStop.disabled = false;
                showNotification("🔴 Perekaman video dimulai (Media Stream)");
            });
        });
    }

    if (btnStreamPause) {
        btnStreamPause.addEventListener("click", () => {
            fetch("/api/camera/pause", { method: "POST" })
            .then(r => r.json())
            .then(res => {
                if (res.paused) {
                    setBadge("⏸ REKAMAN DIPAUS", "#FBBF24");
                    if (statusCam) statusCam.textContent = "⏸ REKAMAN DIPAUS";
                } else {
                    setBadge("🔴 RECORDING VIDEO...", "#FF5E62");
                    if (statusCam) statusCam.textContent = "🔴 REKAMAN AKTIF";
                }
            })
            .catch(err => console.error("Error pausing camera:", err));
        });
    }

    if (btnStreamStop) {
        btnStreamStop.addEventListener("click", () => {
            const noBlok = (inputNoBlok ? inputNoBlok.value.trim() : "default") || "default";
            setBadge("⏳ Menghentikan & Menyimpan Video...", "#FBBF24");
            btnStreamStop.disabled = true;

            const resetUIAfterStop = () => {
                if (recIndicator) recIndicator.style.display = "none";
                setBadge("⏹ VIDEO REKAMAN TERSIMPAN", "#00F5D4");
                if (statusCam) statusCam.textContent = "📷 KAMERA: STREAMING LIVE";
                if (btnStreamStart) btnStreamStart.disabled = false;
                if (btnStreamStop) btnStreamStop.disabled = true;
            };

            const safetyTimer = setTimeout(() => {
                console.warn("Safety reset for video stop recording triggered.");
                resetUIAfterStop();
                showNotification("⏹ Perekaman video dihentikan.", "info");
            }, 3500);

            // 1. Stop Client MediaRecorder if active
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                try {
                    mediaRecorder.stop();
                    mediaRecorder.onstop = () => {
                        if (recordedVideoChunks.length > 0) {
                            const blob = new Blob(recordedVideoChunks, { type: mediaRecorder.mimeType || "video/webm" });
                            const formData = new FormData();
                            formData.append("file", blob, `REC_${noBlok}.webm`);
                            formData.append("blok", noBlok);
                            fetch("/api/camera/upload_video", { method: "POST", body: formData })
                            .then(r => r.json())
                            .then(res => {
                                console.log("Uploaded client recorded video:", res);
                                if (res.success && res.url) {
                                    addVideoToAlbum(res.url, res.filepath, res.filename);
                                }
                            })
                            .catch(e => console.error("Upload video err:", e));
                        }
                    };
                } catch(e) { console.warn("Error stopping client MediaRecorder:", e); }
            }
            
            // 2. Call Backend Stop Recording API
            fetch("/api/camera/stop_recording", { method: "POST" })
            .then(r => r.json())
            .then(res => {
                clearTimeout(safetyTimer);
                resetUIAfterStop();
                if (res.filepath) lastRecordedVideoPath = res.filepath;

                const vFilename = res.filename || (res.filepath ? res.filepath.split(/[/\\]/).pop() : "REC_video.avi");
                const vUrl = res.url || `/videos/${vFilename}`;
                addVideoToAlbum(vUrl, res.filepath, vFilename);

                showNotification(`✅ Perekaman dihentikan! Video tersimpan: ${vFilename}`, "success");
            })
            .catch(err => {
                console.error("Error stopping recording:", err);
                clearTimeout(safetyTimer);
                resetUIAfterStop();
                showNotification("✅ Perekaman dihentikan! Video tersimpan.", "success");
            });
        });
    }

    // Live Camera Zoom / Scale Controller
    function applyCameraZoom(scaleVal) {
        const val = parseFloat(scaleVal) || 1.0;
        const directImg = document.getElementById("mjpeg-direct-img");
        const directImgCam2 = document.getElementById("mjpeg-direct-img-cam2");
        const canvasElem = document.getElementById("camera-stream-element");
        const lbl = document.getElementById("lbl-crop-scale");
        
        if (directImg) {
            directImg.style.transform = `scale(${val})`;
            directImg.style.transformOrigin = "center center";
            directImg.style.transition = "transform 0.05s linear";
        }
        if (directImgCam2) {
            directImgCam2.style.transform = `scale(${val})`;
            directImgCam2.style.transformOrigin = "center center";
            directImgCam2.style.transition = "transform 0.05s linear";
        }
        if (canvasElem) {
            canvasElem.style.transform = `scale(${val})`;
            canvasElem.style.transformOrigin = "center center";
            canvasElem.style.transition = "transform 0.05s linear";
        }
        if (lbl) {
            lbl.textContent = `${val.toFixed(1)}x`;
        }
    }

    if (sliderCropScale) {
        sliderCropScale.addEventListener("input", (e) => {
            applyCameraZoom(e.target.value);
        });
    }

    if (btnResetCrop) {
        btnResetCrop.addEventListener("click", () => {
            const slider = document.getElementById("slider-crop-scale");
            const lbl = document.getElementById("lbl-crop-scale");
            if (slider) slider.value = "1.0";
            if (lbl) lbl.textContent = "1.0x";
            applyCameraZoom(1.0);
        });
    }

    const selGimbalStep = document.getElementById("web-gimbal-step");
    const btnRollLeft = document.getElementById("btn-web-roll-left");
    const btnRollFlat = document.getElementById("btn-web-roll-flat");
    const btnRollRight = document.getElementById("btn-web-roll-right");

    let isSendingGimbal = false;
    let pendingGimbalDir = null;

    function sendGimbalDirection(dirCommand) {
        if (!dirCommand) return;
        if (isSendingGimbal) {
            pendingGimbalDir = dirCommand;
            return;
        }
        isSendingGimbal = true;
        const stepVal = parseFloat(selGimbalStep ? selGimbalStep.value : 10) || 10;
        fetchWithTimeout("/api/gimbal/direction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ direction: dirCommand, step: stepVal }),
            timeout: 2000
        }).then(res => res.json())
        .then(data => console.log("Gimbal command OK:", data))
        .catch(err => console.error("Gimbal API Error:", err))
        .finally(() => {
            isSendingGimbal = false;
            if (pendingGimbalDir) {
                const next = pendingGimbalDir;
                pendingGimbalDir = null;
                sendGimbalDirection(next);
            }
        });
    }

    // =============================================================================
    // 3-AXIS SERVO GIMBAL (PCA9685 I2C) - EXCLUSIVE TO KAMERA 1 (SICK)
    // =============================================================================
    const servoGimbalButtons = document.querySelectorAll(".btn-servo-gimbal, .gimbal-dpad-grid-v2 button:not(.btn-stepper-dir)");

    if (servoGimbalButtons) {
        servoGimbalButtons.forEach(btn => {
            const dirAttr = (btn.getAttribute("data-dir") || "").toUpperCase();
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                console.log("[SERVO GIMBAL I2C] Direction:", dirAttr);
                sendGimbalDirection(dirAttr);
            });
        });
    }

    if (btnRollLeft) btnRollLeft.addEventListener("click", () => sendGimbalDirection("ROLL_LEFT"));
    if (btnRollFlat) btnRollFlat.addEventListener("click", () => sendGimbalDirection("ROLL_FLAT"));
    if (btnRollRight) btnRollRight.addEventListener("click", () => sendGimbalDirection("ROLL_RIGHT"));



    function updateIframeCrop() {
        const iframe = document.getElementById("camera-iframe-element");
        if (!iframe) return;
        const scale = sliderCropScale ? sliderCropScale.value : 2.4;
        const posX = sliderCropX ? sliderCropX.value : -110;
        const posY = sliderCropY ? sliderCropY.value : -28;

        if (lblCropScale) lblCropScale.textContent = scale + "x";
        if (lblCropX) lblCropX.textContent = posX + "%";
        if (lblCropY) lblCropY.textContent = posY + "%";

        const sizePct = (parseFloat(scale) * 100).toFixed(0) + "%";

        iframe.style.width = sizePct;
        iframe.style.height = sizePct;
        iframe.style.left = posX + "%";
        iframe.style.top = posY + "%";
    }

    if (sliderCropScale) sliderCropScale.addEventListener("input", updateIframeCrop);
    if (sliderCropX) sliderCropX.addEventListener("input", updateIframeCrop);
    if (sliderCropY) sliderCropY.addEventListener("input", updateIframeCrop);
    if (btnResetCrop) {
        btnResetCrop.addEventListener("click", () => {
            if (sliderCropScale) sliderCropScale.value = 2.4;
            if (sliderCropX) sliderCropX.value = -110;
            if (sliderCropY) sliderCropY.value = -28;
            updateIframeCrop();
        });
    }

    let activePhotoIndex = -1;
    let galleryItemsList = [];

    const btnClearGallery = document.getElementById("btn-clear-gallery");
    const btnDeleteSnap = document.getElementById("btn-delete-snap");
    const btnDownloadSnap = document.getElementById("btn-download-snap");

    function addToGallery(url, filepath) {
        if (!url) return;
        const fname = filepath ? filepath.split(/[/\\]/).pop() : "snapshot.jpg";
        const cleanPath = filepath || url;
        capturedPhotoPaths.push(cleanPath);
        const item = { url: url, filepath: cleanPath, filename: fname, time: new Date().toLocaleTimeString() };
        galleryItemsList.push(item);
        renderGallery();
        updatePreviewWindow(item, galleryItemsList.length - 1);
    }

    function updatePreviewWindow(item, index) {
        const lastImg = document.getElementById("last-snapshot-preview-img");
        const lastEmpty = document.getElementById("last-snapshot-empty");
        const lastTime = document.getElementById("last-snap-time");
        const infoOverlay = document.getElementById("last-snapshot-info-overlay");
        const actionsOverlay = document.getElementById("last-snapshot-actions");
        const filenameLbl = document.getElementById("lbl-snap-filename");

        activePhotoIndex = index;

        if (item && item.url) {
            if (lastImg) { lastImg.src = item.url; lastImg.style.display = "block"; }
            if (lastEmpty) lastEmpty.style.display = "none";
            if (lastTime) lastTime.textContent = item.time || new Date().toLocaleTimeString();
            if (infoOverlay) infoOverlay.style.display = "block";
            if (actionsOverlay) actionsOverlay.style.display = "flex";
            if (filenameLbl) {
                const fname = item.filepath ? item.filepath.split(/[/\\]/).pop() : "snapshot.jpg";
                filenameLbl.textContent = fname;
            }
            if (btnDownloadSnap) {
                btnDownloadSnap.href = item.url;
                btnDownloadSnap.download = item.filepath ? item.filepath.split(/[/\\]/).pop() : "snapshot.jpg";
            }
        } else {
            if (lastImg) { lastImg.src = ""; lastImg.style.display = "none"; }
            if (lastEmpty) lastEmpty.style.display = "block";
            if (lastTime) lastTime.textContent = "BELUM ADA";
            if (infoOverlay) infoOverlay.style.display = "none";
            if (actionsOverlay) actionsOverlay.style.display = "none";
        }

        const thumbs = galleryThumbnails ? galleryThumbnails.querySelectorAll(".thumb-card") : [];
        thumbs.forEach((t, i) => {
            if (i === index) {
                t.style.border = "3px solid #00F5D4";
                t.style.boxShadow = "0 0 10px rgba(0,245,212,0.8), 3px 3px 0px #000";
            } else {
                t.style.border = "3px solid #000";
                t.style.boxShadow = "2px 2px 0px #000";
            }
        });
    }

    function renderGallery() {
        if (!galleryThumbnails) return;
        galleryThumbnails.innerHTML = "";

        if (galleryItemsList.length === 0) {
            const ph = document.createElement("div");
            ph.className = "gallery-placeholder";
            ph.id = "gallery-placeholder";
            ph.style.cssText = "color:#94A3B8;font-size:11px;font-weight:700;width:100%;text-align:center;";
            ph.textContent = "Belum ada foto snapshot yang disimpan";
            galleryThumbnails.appendChild(ph);
            if (galleryCount) galleryCount.textContent = "TOTAL: 0";
            updatePreviewWindow(null, -1);
            return;
        }

        if (galleryCount) galleryCount.textContent = `TOTAL: ${galleryItemsList.length}`;

        galleryItemsList.forEach((item, idx) => {
            const card = document.createElement("div");
            card.className = "thumb-card";
            card.style.cssText = "position:relative;width:76px;height:56px;border:3px solid #000;border-radius:6px;overflow:hidden;flex-shrink:0;cursor:pointer;background:#000;box-shadow:2px 2px 0px #000;transition:transform 0.15s, border-color 0.15s;";
            card.innerHTML = `
                <img src="${item.url}" alt="Snap ${idx+1}" style="width:100%;height:100%;object-fit:cover;">
                <button type="button" class="thumb-del-btn" style="position:absolute;top:2px;right:2px;background:#EF4444;color:#FFF;border:1px solid #000;font-size:9px;width:16px;height:16px;line-height:14px;text-align:center;padding:0;font-weight:bold;cursor:pointer;display:none;border-radius:3px;">×</button>
            `;

            const delBtn = card.querySelector(".thumb-del-btn");
            card.addEventListener("mouseenter", () => { if (delBtn) delBtn.style.display = "block"; card.style.transform = "scale(1.05)"; });
            card.addEventListener("mouseleave", () => { if (delBtn) delBtn.style.display = "none"; card.style.transform = "scale(1)"; });

            card.addEventListener("click", (e) => {
                if (e.target === delBtn) {
                    deletePhoto(idx);
                } else {
                    updatePreviewWindow(item, idx);
                    openMediaModal("photo", item, idx);
                }
            });

            galleryThumbnails.appendChild(card);
        });

        if (activePhotoIndex >= 0 && activePhotoIndex < galleryItemsList.length) {
            updatePreviewWindow(galleryItemsList[activePhotoIndex], activePhotoIndex);
        } else {
            updatePreviewWindow(galleryItemsList[galleryItemsList.length - 1], galleryItemsList.length - 1);
        }
    }

    const lastSnapImg = document.getElementById("last-snapshot-preview-img");
    if (lastSnapImg) {
        lastSnapImg.addEventListener("click", () => {
            if (activePhotoIndex >= 0 && activePhotoIndex < galleryItemsList.length) {
                openMediaModal("photo", galleryItemsList[activePhotoIndex], activePhotoIndex);
            }
        });
    }

    function deletePhoto(index) {
        if (index >= 0 && index < galleryItemsList.length) {
            galleryItemsList.splice(index, 1);
            capturedPhotoPaths.splice(index, 1);
            if (activePhotoIndex >= galleryItemsList.length) {
                activePhotoIndex = galleryItemsList.length - 1;
            }
            renderGallery();
        }
    }

    if (btnClearGallery) {
        btnClearGallery.addEventListener("click", () => {
            if (galleryItemsList.length === 0) return;
            if (confirm("Hapus semua foto snapshot dari galeri saat ini?")) {
                galleryItemsList = [];
                capturedPhotoPaths = [];
                activePhotoIndex = -1;
                renderGallery();
            }
        });
    }

    if (btnDeleteSnap) {
        btnDeleteSnap.addEventListener("click", () => {
            if (activePhotoIndex >= 0) {
                deletePhoto(activePhotoIndex);
            }
        });
    }

    // =============================================================================
    // MEDIA LIGHTBOX MODAL POPUP (PHOTO & VIDEO FULL-SCREEN PREVIEW)
    // =============================================================================
    const modalBackdrop = document.getElementById("media-modal-backdrop");
    const modalContent = document.getElementById("media-modal-content");
    const modalTypeIcon = document.getElementById("modal-type-icon");
    const modalTitle = document.getElementById("modal-title");
    const modalPhotoElem = document.getElementById("modal-photo-element");
    const modalVideoElem = document.getElementById("modal-video-element");
    const modalFilenameLbl = document.getElementById("modal-filename-label");
    const modalTimeLbl = document.getElementById("modal-time-label");
    const btnModalDownload = document.getElementById("btn-modal-download");
    const btnModalDelete = document.getElementById("btn-modal-delete");
    const btnCloseModal = document.getElementById("btn-close-modal");

    let currentModalMedia = null; // { type: 'photo'|'video', item: item, index: index }

    function openMediaModal(type, item, index) {
        if (!item || !item.url || !modalBackdrop) return;
        currentModalMedia = { type: type, item: item, index: index };

        const fname = item.filename || (item.filepath ? item.filepath.split(/[/\\]/).pop() : (type === "photo" ? "snapshot.jpg" : "recording.mp4"));

        if (modalFilenameLbl) modalFilenameLbl.textContent = fname;
        if (modalTimeLbl) modalTimeLbl.textContent = "📅 TANGGAL: " + (item.time || new Date().toLocaleTimeString());
        if (btnModalDownload) {
            btnModalDownload.href = item.url;
            btnModalDownload.download = fname;
        }

        if (type === "photo") {
            if (modalTypeIcon) modalTypeIcon.textContent = "📸";
            if (modalTitle) modalTitle.textContent = "POPUP SNAPSHOT FOTO";
            if (modalVideoElem) { modalVideoElem.pause(); modalVideoElem.src = ""; modalVideoElem.style.display = "none"; }
            if (modalPhotoElem) { modalPhotoElem.src = item.url; modalPhotoElem.style.display = "block"; }
        } else if (type === "video") {
            if (modalTypeIcon) modalTypeIcon.textContent = "🎬";
            if (modalTitle) modalTitle.textContent = "POPUP PEMUTAR VIDEO";
            if (modalPhotoElem) { modalPhotoElem.src = ""; modalPhotoElem.style.display = "none"; }
            if (modalVideoElem) {
                modalVideoElem.pause();
                modalVideoElem.src = item.url;
                modalVideoElem.load();
                modalVideoElem.style.display = "block";
                
                const playPromise = modalVideoElem.play();
                if (playPromise !== undefined) {
                    playPromise.catch(e => console.log("Autoplay paused by browser policy:", e));
                }
            }
        }

        modalBackdrop.style.display = "flex";
    }

    function closeMediaModal() {
        if (!modalBackdrop) return;
        if (modalVideoElem) {
            modalVideoElem.pause();
            modalVideoElem.src = "";
        }
        if (modalPhotoElem) {
            modalPhotoElem.src = "";
        }
        modalBackdrop.style.display = "none";
        currentModalMedia = null;
    }

    if (btnCloseModal) btnCloseModal.addEventListener("click", closeMediaModal);

    if (modalBackdrop) {
        modalBackdrop.addEventListener("click", (e) => {
            if (e.target === modalBackdrop) closeMediaModal();
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modalBackdrop && modalBackdrop.style.display !== "none") {
            closeMediaModal();
        }
    });

    if (btnModalDelete) {
        btnModalDelete.addEventListener("click", () => {
            if (!currentModalMedia) return;
            if (currentModalMedia.type === "photo") {
                deletePhoto(currentModalMedia.index);
            } else if (currentModalMedia.type === "video") {
                deleteVideo(currentModalMedia.index);
            }
            closeMediaModal();
        });
    }

    // (Gimbal PCA9685 I2C event listeners are handled exclusively above)

    // =============================================================================
    // VIDEO ALBUM & PREVIEW PLAYER MANAGEMENT
    // =============================================================================
    let activeVideoIndex = -1;
    let recordedVideoList = [];

    const videoGalleryThumbnails = document.getElementById("video-gallery-thumbnails");
    const videoGalleryCount = document.getElementById("video-gallery-count");
    const btnClearVideoGallery = document.getElementById("btn-clear-video-gallery");
    const btnDeleteVideo = document.getElementById("btn-delete-video");
    const btnDownloadVideo = document.getElementById("btn-download-video");

    function updateVideoPreviewWindow(item, index) {
        const lastVideoPlayer = document.getElementById("last-video-preview-player");
        const lastVideoEmpty = document.getElementById("last-video-empty");
        const lastVideoTime = document.getElementById("last-video-time");
        const videoInfoOverlay = document.getElementById("last-video-info-overlay");
        const videoActionsOverlay = document.getElementById("last-video-actions");
        const videoFilenameLbl = document.getElementById("lbl-video-filename");

        activeVideoIndex = index;

        if (item && item.url) {
            if (lastVideoPlayer) {
                lastVideoPlayer.src = item.url;
                lastVideoPlayer.style.display = "block";
            }
            if (lastVideoEmpty) lastVideoEmpty.style.display = "none";
            if (lastVideoTime) lastVideoTime.textContent = item.time || new Date().toLocaleTimeString();
            if (videoInfoOverlay) videoInfoOverlay.style.display = "block";
            if (videoActionsOverlay) videoActionsOverlay.style.display = "flex";
            if (videoFilenameLbl) {
                const fname = item.filename || (item.filepath ? item.filepath.split(/[/\\]/).pop() : "recording.mp4");
                videoFilenameLbl.textContent = fname;
            }
            if (btnDownloadVideo) {
                btnDownloadVideo.href = item.url;
                btnDownloadVideo.download = item.filename || (item.filepath ? item.filepath.split(/[/\\]/).pop() : "recording.mp4");
            }
        } else {
            if (lastVideoPlayer) { lastVideoPlayer.src = ""; lastVideoPlayer.style.display = "none"; }
            if (lastVideoEmpty) lastVideoEmpty.style.display = "block";
            if (lastVideoTime) lastVideoTime.textContent = "BELUM ADA";
            if (videoInfoOverlay) videoInfoOverlay.style.display = "none";
            if (videoActionsOverlay) videoActionsOverlay.style.display = "none";
        }

        const vThumbs = videoGalleryThumbnails ? videoGalleryThumbnails.querySelectorAll(".video-thumb-card") : [];
        vThumbs.forEach((t, i) => {
            if (i === index) {
                t.style.border = "3px solid #FF5E62";
                t.style.boxShadow = "0 0 10px rgba(255,94,98,0.8), 3px 3px 0px #000";
            } else {
                t.style.border = "3px solid #000";
                t.style.boxShadow = "2px 2px 0px #000";
            }
        });
    }

    function renderVideoGallery() {
        if (!videoGalleryThumbnails) return;
        videoGalleryThumbnails.innerHTML = "";

        if (recordedVideoList.length === 0) {
            const ph = document.createElement("div");
            ph.className = "gallery-placeholder";
            ph.id = "video-gallery-placeholder";
            ph.style.cssText = "color:#64748B;font-size:11px;font-weight:700;width:100%;text-align:center;font-family:monospace;";
            ph.textContent = "[ ALBUM VIDEO KOSONG - REKAMAN AKAN TERSIMPAN DI SINI ]";
            videoGalleryThumbnails.appendChild(ph);
            if (videoGalleryCount) videoGalleryCount.textContent = "TOTAL: 0";
            updateVideoPreviewWindow(null, -1);
            return;
        }

        if (videoGalleryCount) videoGalleryCount.textContent = `TOTAL: ${recordedVideoList.length}`;

        recordedVideoList.forEach((item, idx) => {
            const card = document.createElement("div");
            card.className = "video-thumb-card";
            card.style.cssText = "position:relative;width:96px;height:64px;border:3px solid #000;border-radius:6px;overflow:hidden;flex-shrink:0;cursor:pointer;background:#050B14;box-shadow:2px 2px 0px #000;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:transform 0.15s, border-color 0.15s;";
            card.innerHTML = `
                <div style="font-size:22px;filter:drop-shadow(0 0 4px #FF5E62);">🎬</div>
                <div style="position:absolute;bottom:2px;left:2px;right:2px;background:rgba(15,23,42,0.85);color:#FFF;font-size:8px;font-family:monospace;padding:1px 3px;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    ${item.filename || 'VIDEO'}
                </div>
                <button type="button" class="vthumb-del-btn" style="position:absolute;top:2px;right:2px;background:#EF4444;color:#FFF;border:1px solid #000;font-size:9px;width:16px;height:16px;line-height:14px;text-align:center;padding:0;font-weight:bold;cursor:pointer;display:none;border-radius:3px;z-index:5;">×</button>
            `;

            const delBtn = card.querySelector(".vthumb-del-btn");
            card.addEventListener("mouseenter", () => { if (delBtn) delBtn.style.display = "block"; card.style.transform = "scale(1.05)"; });
            card.addEventListener("mouseleave", () => { if (delBtn) delBtn.style.display = "none"; card.style.transform = "scale(1)"; });

            card.addEventListener("click", (e) => {
                if (e.target === delBtn) {
                    deleteVideo(idx);
                } else {
                    updateVideoPreviewWindow(item, idx);
                    openMediaModal("video", item, idx);
                }
            });

            videoGalleryThumbnails.appendChild(card);
        });

        if (activeVideoIndex >= 0 && activeVideoIndex < recordedVideoList.length) {
            updateVideoPreviewWindow(recordedVideoList[activeVideoIndex], activeVideoIndex);
        } else {
            updateVideoPreviewWindow(recordedVideoList[recordedVideoList.length - 1], recordedVideoList.length - 1);
        }
    }

    function deleteVideo(index) {
        if (index >= 0 && index < recordedVideoList.length) {
            recordedVideoList.splice(index, 1);
            if (activeVideoIndex >= recordedVideoList.length) {
                activeVideoIndex = recordedVideoList.length - 1;
            }
            renderVideoGallery();
        }
    }

    function addVideoToAlbum(videoUrl, videoPath, filename) {
        if (!videoUrl) return;
        const item = {
            url: videoUrl,
            filepath: videoPath || videoUrl,
            filename: filename || (videoPath ? videoPath.split(/[/\\]/).pop() : "recording.mp4"),
            time: new Date().toLocaleTimeString()
        };
        recordedVideoList.push(item);
        if (typeof lastRecordedVideoPath !== "undefined") {
            lastRecordedVideoPath = videoPath || videoUrl;
        }
        renderVideoGallery();
        updateVideoPreviewWindow(item, recordedVideoList.length - 1);
    }

    if (btnClearVideoGallery) {
        btnClearVideoGallery.addEventListener("click", () => {
            if (recordedVideoList.length === 0) return;
            if (confirm("Hapus semua video rekaman dari album galeri saat ini?")) {
                recordedVideoList = [];
                activeVideoIndex = -1;
                renderVideoGallery();
            }
        });
    }

    if (btnDeleteVideo) {
        btnDeleteVideo.addEventListener("click", () => {
            if (activeVideoIndex >= 0) {
                deleteVideo(activeVideoIndex);
            }
        });
    }

    if (btnCapturePhoto) {
        btnCapturePhoto.addEventListener("click", () => {
            btnCapturePhoto.textContent = "📸 SEDANG MENGAMBIL FOTO...";
            btnCapturePhoto.disabled = true;
            const blockName = (inputNoBlok ? inputNoBlok.value.trim() : "default") || "default";
            const currentScale = parseFloat(sliderCropScale ? sliderCropScale.value : "1.0") || 1.0;

            const safetyTimeout = setTimeout(() => {
                btnCapturePhoto.textContent = "📸 AMBIL SNAPSHOT FOTO";
                btnCapturePhoto.disabled = false;
            }, 6000);

            function addToGallery(url, filepath) {
                capturedPhotoPaths.push(filepath);
                const item = { url: url, filepath: filepath, time: new Date().toLocaleTimeString() };
                galleryItemsList.push(item);
                renderGallery();
                updatePreviewWindow(item, galleryItemsList.length - 1);
            }

            function captureViaBackend() {
                fetch("/api/camera/capture", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ blok: blockName, scale: currentScale })
                }).then(res => res.json())
                .then(data => { if (data.success) addToGallery(data.url, data.filepath); else alert("Gagal: " + data.message); })
                .catch(() => alert("Error backend saat capture."))
                .finally(() => { 
                    clearTimeout(safetyTimeout);
                    btnCapturePhoto.textContent = "📸 AMBIL SNAPSHOT FOTO"; 
                    btnCapturePhoto.disabled = false; 
                });
            }

            // Try capturing active client DOM image / video element with crop scale applied
            const videoElem = document.getElementById("client-webcam-element");
            const imgElem = document.getElementById("mjpeg-direct-img");
            const canvasElem = document.getElementById("camera-stream-element");

            let sourceElem = null;
            if (videoElem && videoElem.style.display !== "none" && videoElem.readyState >= 2) {
                sourceElem = videoElem;
            } else if (imgElem && imgElem.style.display !== "none" && imgElem.complete && imgElem.naturalWidth > 0) {
                sourceElem = imgElem;
            } else if (canvasElem && canvasElem.style.display !== "none") {
                sourceElem = canvasElem;
            }

            if (sourceElem) {
                try {
                    const sw = sourceElem.naturalWidth || sourceElem.videoWidth || sourceElem.width || 1280;
                    const sh = sourceElem.naturalHeight || sourceElem.videoHeight || sourceElem.height || 720;
                    
                    const tempCanvas = document.createElement("canvas");
                    tempCanvas.width = sw;
                    tempCanvas.height = sh;
                    const ctx = tempCanvas.getContext("2d");
                    
                    if (currentScale > 1.0) {
                        const cropW = sw / currentScale;
                        const cropH = sh / currentScale;
                        const cropX = (sw - cropW) / 2;
                        const cropY = (sh - cropH) / 2;
                        ctx.drawImage(sourceElem, cropX, cropY, cropW, cropH, 0, 0, sw, sh);
                    } else {
                        ctx.drawImage(sourceElem, 0, 0, sw, sh);
                    }
                    
                    tempCanvas.toBlob((blob) => {
                        if (blob) {
                            const formData = new FormData();
                            formData.append("file", blob, "snapshot.jpg");
                            formData.append("blok", blockName);
                            formData.append("scale", currentScale);
                            
                            fetch("/api/camera/capture_canvas", {
                                method: "POST",
                                body: formData
                            })
                            .then(r => r.json())
                            .then(data => {
                                if (data.success) {
                                    addToGallery(data.url, data.filepath);
                                    clearTimeout(safetyTimeout);
                                    btnCapturePhoto.textContent = "📸 AMBIL SNAPSHOT FOTO";
                                    btnCapturePhoto.disabled = false;
                                } else {
                                    captureViaBackend();
                                }
                            })
                            .catch(() => captureViaBackend());
                        } else {
                            captureViaBackend();
                        }
                    }, "image/jpeg", 0.98);
                    return;
                } catch(e) {
                    console.warn("Client canvas crop capture exception, falling back to backend:", e);
                }
            }

            captureViaBackend();
        });
    }

    // =============================================================================
    // STREAM MODE CONTROLLER: NORMAL (VIGI) vs AI GANODERMA (YOLO26n-seg)
    // =============================================================================
    let currentStreamMode = 'normal'; // 'normal' | 'ai'
    let aiPollingTimer = null;
    const btnModeNormal = document.getElementById("btn-mode-normal");
    const btnModeAi = document.getElementById("btn-mode-ai");
    const imgCam2Stream = document.getElementById("mjpeg-direct-img-cam2");
    const liveStreamBadge = document.getElementById("live-stream-badge");
    const aiTelemetryBadge = document.getElementById("ai-telemetry-badge");

    function setStreamMode(mode) {
        currentStreamMode = mode;
        if (mode === 'ai') {
            if (btnModeAi) {
                btnModeAi.style.background = "#00F5D4";
                btnModeAi.style.color = "#000";
            }
            if (btnModeNormal) {
                btnModeNormal.style.background = "#1E293B";
                btnModeNormal.style.color = "#94A3B8";
            }
            if (imgCam2Stream) {
                imgCam2Stream.src = "/api/ai/stream";
            }
            if (liveStreamBadge) {
                liveStreamBadge.textContent = "● AI GANODERMA LIVE";
                liveStreamBadge.style.background = "#8B5CF6";
            }
            if (aiTelemetryBadge) {
                aiTelemetryBadge.style.display = "inline-block";
                aiTelemetryBadge.textContent = "● AI: MEMUAT...";
            }
            startAiTelemetryPolling();
            if (typeof showNotification === "function") {
                showNotification("🧠 Mode AI Ganoderma Aktif (YOLO26n-seg TensorRT)", "info");
            }
        } else {
            if (btnModeNormal) {
                btnModeNormal.style.background = "#00F5D4";
                btnModeNormal.style.color = "#000";
            }
            if (btnModeAi) {
                btnModeAi.style.background = "#1E293B";
                btnModeAi.style.color = "#94A3B8";
            }
            if (imgCam2Stream) {
                imgCam2Stream.src = "/api/camera2/stream";
            }
            if (liveStreamBadge) {
                liveStreamBadge.textContent = "● TP-LINK VIGI LIVE";
                liveStreamBadge.style.background = "#FF5E62";
            }
            if (aiTelemetryBadge) {
                aiTelemetryBadge.style.display = "none";
            }
            stopAiTelemetryPolling();
            if (typeof showNotification === "function") {
                showNotification("📷 Mode Normal Aktif (Kamera TP-Link VIGI)", "info");
            }
        }
    }

    function startAiTelemetryPolling() {
        stopAiTelemetryPolling();
        pollAiStatus();
        aiPollingTimer = setInterval(pollAiStatus, 1500);
    }

    function stopAiTelemetryPolling() {
        if (aiPollingTimer) {
            clearInterval(aiPollingTimer);
            aiPollingTimer = null;
        }
    }

    function pollAiStatus() {
        if (currentStreamMode !== 'ai') return;
        fetchWithTimeout("/api/ai/status", { timeout: 2000 })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.ai) {
                    const ai = data.ai;
                    const det = ai.detections || 0;
                    const streamFps = ai.stream_fps || (ai.processing_fps ? 20.0 : 0);
                    const inferFps = ai.processing_fps || 0;
                    const conf = ai.max_confidence ? (ai.max_confidence * 100).toFixed(0) + "%" : "";
                    if (aiTelemetryBadge) {
                        aiTelemetryBadge.textContent = `● AI: ${det} DETEKSI | ${Math.round(streamFps)} FPS`;
                        if (det > 0) {
                            aiTelemetryBadge.style.background = "#EF4444"; // Red alert for detection!
                            aiTelemetryBadge.style.color = "#FFF";
                        } else {
                            aiTelemetryBadge.style.background = "#8B5CF6"; // Purple normal
                            aiTelemetryBadge.style.color = "#FFF";
                        }
                    }
                }
            })
            .catch(() => {
                if (aiTelemetryBadge) {
                    aiTelemetryBadge.textContent = "● AI: RECONNECTING...";
                    aiTelemetryBadge.style.background = "#64748B";
                }
            });
    }

    if (btnModeNormal) {
        btnModeNormal.addEventListener("click", () => setStreamMode('normal'));
    }
    if (btnModeAi) {
        btnModeAi.addEventListener("click", () => setStreamMode('ai'));
    }

    // =============================================================================
    // OPTICAL ZOOM CONTROLLER (TP-LINK VIGI S345ZI MOTORIZED LENS ONVIF)
    // =============================================================================
    const btnOpticalZoomIn = document.getElementById("btn-optical-zoom-in");
    const btnOpticalZoomOut = document.getElementById("btn-optical-zoom-out");
    const btnOpticalZoomReset = document.getElementById("btn-optical-zoom-reset");
    const sliderOpticalZoom = document.getElementById("slider-optical-zoom");
    const lblOpticalZoom = document.getElementById("lbl-optical-zoom");
    const opticalPresets = document.querySelectorAll(".btn-optical-preset");

    function sendOpticalZoom(payload) {
        if (lblOpticalZoom) {
            lblOpticalZoom.textContent = "MOVING...";
            lblOpticalZoom.style.color = "#FACC15";
        }
        return fetchWithTimeout("/api/camera/optical_zoom", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            timeout: 5000
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (payload.position !== undefined) {
                    updateOpticalZoomLabel(payload.position);
                } else if (payload.action === 'reset') {
                    updateOpticalZoomLabel(0.0);
                } else {
                    if (lblOpticalZoom) {
                        lblOpticalZoom.textContent = payload.action === 'in' ? "TELE (+)" : "WIDE (-)";
                        lblOpticalZoom.style.color = "#00F5D4";
                    }
                }
                if (typeof showNotification === "function") {
                    showNotification(`🔍 ${data.message || 'Optical Zoom disesuaikan'}`, "success");
                }
            } else {
                console.warn("Optical Zoom failed:", data.message);
                if (lblOpticalZoom) {
                    lblOpticalZoom.textContent = "ERR";
                    lblOpticalZoom.style.color = "#EF4444";
                }
            }
            return data;
        })
        .catch(err => {
            console.error("Optical Zoom network error:", err);
            if (lblOpticalZoom) {
                lblOpticalZoom.textContent = "OFFLINE";
                lblOpticalZoom.style.color = "#EF4444";
            }
        });
    }

    function updateOpticalZoomLabel(pos) {
        const p = parseFloat(pos);
        if (sliderOpticalZoom) sliderOpticalZoom.value = p;
        if (lblOpticalZoom) {
            if (p <= 0.05) {
                lblOpticalZoom.textContent = "1.0x (WIDE)";
            } else if (p >= 0.95) {
                lblOpticalZoom.textContent = "4.0x (MAX TELE)";
            } else {
                const approx = (1.0 + p * 3.0).toFixed(1);
                lblOpticalZoom.textContent = `${approx}x OPTICAL`;
            }
            lblOpticalZoom.style.color = "#00F5D4";
        }
    }

    if (btnOpticalZoomIn) {
        btnOpticalZoomIn.addEventListener("click", () => {
            sendOpticalZoom({ action: "in", step: 0.15 });
        });
    }

    if (btnOpticalZoomOut) {
        btnOpticalZoomOut.addEventListener("click", () => {
            sendOpticalZoom({ action: "out", step: 0.15 });
        });
    }

    if (btnOpticalZoomReset) {
        btnOpticalZoomReset.addEventListener("click", () => {
            sendOpticalZoom({ action: "reset" });
        });
    }

    if (sliderOpticalZoom) {
        sliderOpticalZoom.addEventListener("change", (e) => {
            const pos = parseFloat(e.target.value);
            sendOpticalZoom({ position: pos });
        });
        sliderOpticalZoom.addEventListener("input", (e) => {
            updateOpticalZoomLabel(e.target.value);
        });
    }

    if (opticalPresets && opticalPresets.length > 0) {
        opticalPresets.forEach(btn => {
            btn.addEventListener("click", () => {
                const pos = parseFloat(btn.dataset.pos || "0");
                sendOpticalZoom({ position: pos });
            });
        });
    }

    // =============================================================================
    // CAPTURE PHOTO SNAPSHOT (SUPPORTS NORMAL VIGI & AI GANODERMA MODES)
    // =============================================================================
    const btnCapturePhotoCam2 = document.getElementById("btn-capture-photo-cam2");
    if (btnCapturePhotoCam2) {
        btnCapturePhotoCam2.addEventListener("click", () => {
            btnCapturePhotoCam2.textContent = "📸 SEDANG MENGAMBIL FOTO...";
            btnCapturePhotoCam2.disabled = true;
            const blockName = (inputNoBlok ? inputNoBlok.value.trim() : (currentStreamMode === 'ai' ? "AI_GANO" : "TPLINK")) || "TPLINK";

            // If in AI mode, capture from AI annotated port 8080!
            const endpoint = (currentStreamMode === 'ai') ? "/api/ai/capture" : "/api/camera2/capture";

            fetchWithTimeout(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ blok: blockName }),
                timeout: 6000
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.url) {
                    addToGallery(data.url, data.filepath || data.filename);
                    if (typeof showNotification === "function") {
                        const modeMsg = (currentStreamMode === 'ai') ? "Snapshot AI Ganoderma" : "Snapshot Kamera";
                        showNotification(`✅ ${modeMsg} tersimpan: ${data.filename || ''}`, "success");
                    }
                } else {
                    alert("Gagal mengambil snapshot: " + (data.message || "Pastikan Kamera / AI aktif"));
                }
            })
            .catch(err => {
                console.error("Capture Cam2 error:", err);
                alert("Gagal mengambil snapshot: " + err);
            })
            .finally(() => {
                btnCapturePhotoCam2.textContent = "📸 AMBIL SNAPSHOT FOTO";
                btnCapturePhotoCam2.disabled = false;
            });
        });
    }
    // =============================================================================
    // STEP 3: SENSOR ENGINE & DB SAVE
    // =============================================================================
    
    if (btnSensorRead) {
        btnSensorRead.addEventListener("click", () => {
            btnSensorRead.textContent = "⏳ SEDANG MEMBACA SENSOR...";
            btnSensorRead.disabled = true;

            fetch("/api/sensor/read", { method: "POST" })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        latestSensorReading = data.reading;
                        updateSensorGaugesDisplay(data.reading);
                        
                        // Update sensor mode indicator
                        const modeStatus = document.getElementById("mode-sensor-status");
                        if (modeStatus) {
                            modeStatus.textContent = data.mode;
                            modeStatus.className = "mode-val text-green";
                        }
                        
                        if (statusSensor) statusSensor.textContent = `🔌 SENSOR ENGINE: ${data.mode}`;
                    } else {
                        alert("Error sensor: " + data.message);
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert("Gagal membaca sensor Modbus.");
                })
                .finally(() => {
                    btnSensorRead.textContent = "🔄 BACA SENSOR NPK";
                    btnSensorRead.disabled = false;
                });
        });
    }

    function updateSensorGaugesDisplay(tel) {
        // Nitrogen (max 500)
        if (sensorValN) sensorValN.textContent = tel.nitrogen;
        if (sensorFillN) sensorFillN.style.width = Math.min(100, (tel.nitrogen / 500) * 100) + "%";

        // Phosphor (max 500)
        if (sensorValP) sensorValP.textContent = tel.phosphor;
        if (sensorFillP) sensorFillP.style.width = Math.min(100, (tel.phosphor / 500) * 100) + "%";

        // Kalium (max 500)
        if (sensorValK) sensorValK.textContent = tel.kalium;
        if (sensorFillK) sensorFillK.style.width = Math.min(100, (tel.kalium / 500) * 100) + "%";

        // pH (max 14)
        if (sensorValPh) sensorValPh.textContent = tel.ph.toFixed(1);
        if (sensorPhPointer) sensorPhPointer.style.left = Math.min(100, (tel.ph / 14) * 100) + "%";

        // EC (max 2000)
        if (sensorValEc) sensorValEc.textContent = tel.ec;
        if (sensorFillEc) sensorFillEc.style.width = Math.min(100, (tel.ec / 2000) * 100) + "%";

        // Moisture (max 100)
        if (sensorValMoist) sensorValMoist.textContent = tel.moisture.toFixed(1);
        if (sensorFillMoist) sensorFillMoist.style.width = Math.min(100, tel.moisture) + "%";

        // Temperature (max 50)
        if (sensorValTemp) sensorValTemp.textContent = tel.temperature.toFixed(1);
        if (sensorFillTemp) sensorFillTemp.style.width = Math.min(100, (tel.temperature / 50) * 100) + "%";

        // MQ-3 (RAW ADC 0 - 4095)
        const mq3Val = tel.mq3_raw !== undefined ? tel.mq3_raw : (tel.mq3_adc !== undefined ? tel.mq3_adc : (parseFloat(tel.mq3_ppm) || 0));
        if (sensorValMq3) sensorValMq3.textContent = typeof mq3Val === 'number' && !Number.isInteger(mq3Val) ? mq3Val.toFixed(2) : mq3Val;
        if (sensorFillMq3) sensorFillMq3.style.width = Math.min(100, (mq3Val / 4095) * 100) + "%";
        if (sensorDigMq3) {
            sensorDigMq3.textContent = tel.mq3_dig ? "ALARM (HIGH)" : "NORMAL";
            sensorDigMq3.style.background = tel.mq3_dig ? "#ff5252" : "#4ecdc4";
            sensorDigMq3.style.color = tel.mq3_dig ? "#fff" : "#000";
        }

        // MQ-135 (RAW ADC 0 - 4095)
        const mq135Val = tel.mq135_raw !== undefined ? tel.mq135_raw : (tel.mq135_adc !== undefined ? tel.mq135_adc : (parseFloat(tel.mq135_ppm) || 0));
        if (sensorValMq135) sensorValMq135.textContent = typeof mq135Val === 'number' && !Number.isInteger(mq135Val) ? mq135Val.toFixed(2) : mq135Val;
        if (sensorFillMq135) sensorFillMq135.style.width = Math.min(100, (mq135Val / 4095) * 100) + "%";
        if (sensorDigMq135) {
            sensorDigMq135.textContent = tel.mq135_dig ? "ALARM (HIGH)" : "NORMAL";
            sensorDigMq135.style.background = tel.mq135_dig ? "#ff5252" : "#4ecdc4";
            sensorDigMq135.style.color = tel.mq135_dig ? "#fff" : "#000";
        }

        // MQ-138 (RAW ADC 0 - 4095)
        const mq138Val = tel.mq138_raw !== undefined ? tel.mq138_raw : (tel.mq138_adc !== undefined ? tel.mq138_adc : (parseFloat(tel.mq138_ppm) || 0));
        if (sensorValMq138) sensorValMq138.textContent = typeof mq138Val === 'number' && !Number.isInteger(mq138Val) ? mq138Val.toFixed(2) : mq138Val;
        if (sensorFillMq138) sensorFillMq138.style.width = Math.min(100, (mq138Val / 4095) * 100) + "%";
        if (sensorDigMq138) {
            sensorDigMq138.textContent = tel.mq138_dig ? "ALARM (HIGH)" : "NORMAL";
            sensorDigMq138.style.background = tel.mq138_dig ? "#ff5252" : "#4ecdc4";
            sensorDigMq138.style.color = tel.mq138_dig ? "#fff" : "#000";
        }

        // TGS-2600 (RAW ADC 0 - 4095)
        const tgs2600Val = tel.tgs2600_raw !== undefined ? tel.tgs2600_raw : (tel.tgs2600_adc !== undefined ? tel.tgs2600_adc : (parseFloat(tel.tgs2600_ppm) || 0));
        if (sensorValTgs2600) sensorValTgs2600.textContent = typeof tgs2600Val === 'number' && !Number.isInteger(tgs2600Val) ? tgs2600Val.toFixed(2) : tgs2600Val;
        if (sensorFillTgs2600) sensorFillTgs2600.style.width = Math.min(100, (tgs2600Val / 4095) * 100) + "%";
        if (sensorDigTgs2600) {
            sensorDigTgs2600.textContent = tel.tgs2600_dig ? "ALARM (HIGH)" : "NORMAL";
            sensorDigTgs2600.style.background = tel.tgs2600_dig ? "#ff5252" : "#4ecdc4";
            sensorDigTgs2600.style.color = tel.tgs2600_dig ? "#fff" : "#000";
        }

        // TGS-2602 (RAW ADC 0 - 4095)
        const tgs2602Val = tel.tgs2602_raw !== undefined ? tel.tgs2602_raw : (tel.tgs2602_adc !== undefined ? tel.tgs2602_adc : (parseFloat(tel.tgs2602_ppm) || 0));
        if (sensorValTgs2602) sensorValTgs2602.textContent = typeof tgs2602Val === 'number' && !Number.isInteger(tgs2602Val) ? tgs2602Val.toFixed(2) : tgs2602Val;
        if (sensorFillTgs2602) sensorFillTgs2602.style.width = Math.min(100, (tgs2602Val / 4095) * 100) + "%";
        if (sensorDigTgs2602) {
            sensorDigTgs2602.textContent = tel.tgs2602_dig ? "ALARM (HIGH)" : "NORMAL";
            sensorDigTgs2602.style.background = tel.tgs2602_dig ? "#ff5252" : "#4ecdc4";
            sensorDigTgs2602.style.color = tel.tgs2602_dig ? "#fff" : "#000";
        }
    }

    if (btnSensorSave) {
        btnSensorSave.addEventListener("click", () => {
            const corp = inputPerusahaan ? inputPerusahaan.value.trim() : "";
            const garden = inputKebun ? inputKebun.value.trim() : "";
            
            if (!corp || !garden) {
                alert("⚠️ Nama Perusahaan dan Nama Kebun tidak boleh kosong!");
                navigateToStep(0);
                return;
            }

            btnSensorSave.textContent = "⏳ MENYIMPAN...";
            btnSensorSave.disabled = true;

            const payload = {
                nama_perusahaan: corp,
                nama_kebun: garden,
                afdeling: inputAfdeling ? inputAfdeling.value.trim() : "",
                no_blok: inputNoBlok ? inputNoBlok.value.trim() : "",
                tahun_tanam: inputTahun ? inputTahun.value.trim() : "2020",
                luas: parseFloat(inputLuas ? inputLuas.value : "0.0") || 0.0,
                jumlah_terserang: parseInt(inputTerserang ? inputTerserang.value : "0") || 0,
                tanggal_pengambilan: inputTanggal ? inputTanggal.value : todayStr,
                latitude: parseFloat(inputLatitude ? inputLatitude.value : "0.0") || 0.0,
                longitude: parseFloat(inputLongitude ? inputLongitude.value : "0.0") || 0.0,
                nama_lokasi: inputAlamat ? inputAlamat.value.trim() : "",
                
                nitrogen: latestSensorReading.nitrogen || 0,
                phosphor: latestSensorReading.phosphor || 0,
                kalium: latestSensorReading.kalium || 0,
                ph: parseFloat(latestSensorReading.ph || 0) || 0.0,
                ec: latestSensorReading.ec || 0,
                moisture: parseFloat(latestSensorReading.moisture || 0) || 0.0,
                temperature: parseFloat(latestSensorReading.temperature || 0) || 0.0,
                
                // Gas E-Nose Sensor RAW ADC readings (from ESP32 / Mock)
                mq3_raw: latestSensorReading.mq3_raw !== undefined ? latestSensorReading.mq3_raw : (latestSensorReading.mq3_adc || 0),
                mq135_raw: latestSensorReading.mq135_raw !== undefined ? latestSensorReading.mq135_raw : (latestSensorReading.mq135_adc || 0),
                mq138_raw: latestSensorReading.mq138_raw !== undefined ? latestSensorReading.mq138_raw : (latestSensorReading.mq138_adc || 0),
                tgs2600_raw: latestSensorReading.tgs2600_raw !== undefined ? latestSensorReading.tgs2600_raw : (latestSensorReading.tgs2600_adc || 0),
                tgs2602_raw: latestSensorReading.tgs2602_raw !== undefined ? latestSensorReading.tgs2602_raw : (latestSensorReading.tgs2602_adc || 0),
                gas_data: JSON.stringify({
                    mq3: latestSensorReading.mq3_raw ?? latestSensorReading.mq3_adc ?? 0,
                    mq135: latestSensorReading.mq135_raw ?? latestSensorReading.mq135_adc ?? 0,
                    mq138: latestSensorReading.mq138_raw ?? latestSensorReading.mq138_adc ?? 0,
                    tgs2600: latestSensorReading.tgs2600_raw ?? latestSensorReading.tgs2600_adc ?? 0,
                    tgs2602: latestSensorReading.tgs2602_raw ?? latestSensorReading.tgs2602_adc ?? 0
                }),
                
                foto_path: capturedPhotoPaths.join(";"),
                video_path: lastRecordedVideoPath || "",

                // Tree Spatial Compass Attributes
                tree_node_id: treeNodeIdInput ? treeNodeIdInput.value.trim() : "Pohon A",
                tree_age: treeAgeInput ? treeAgeInput.value : "7",
                tree_health_status: treeHealthStatusSelect ? treeHealthStatusSelect.value : "TERTULAR_PARAH",
                spatial_compass_neighbors: JSON.stringify(neighborsData),

                // Surveyor & Field Notes
                surveyor_name: document.getElementById("form-surveyor") ? document.getElementById("form-surveyor").value.trim() : "Tim Survei Lapangan",
                field_notes: document.getElementById("form-catatan") ? document.getElementById("form-catatan").value.trim() : ""
            };

            fetch("/api/inspection/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("🎉 Data inspeksi kebun kelapa sawit berhasil disimpan ke database SQLite lokal!");
                    capturedPhotoPaths = [];
                    navigateToStep(3);
                } else {
                    alert("Gagal menyimpan data: " + data.message);
                }
            })
            .catch(err => {
                console.error(err);
                alert("Error jaringan saat menyimpan data.");
            })
            .finally(() => {
                btnSensorSave.textContent = "💾 SIMPAN DATA";
                btnSensorSave.disabled = false;
            });
        });
    }

    // =============================================================================
    // STEP 4: DATA TABLE (RIWAYAT & RECORD)
    // =============================================================================
    
    const DEFAULT_THUMB_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100' height='100' fill='%231e293b'/><text x='50' y='58' fill='%2394a3b8' font-size='32' font-weight='bold' text-anchor='middle'>📷</text></svg>";

    function loadInspectionHistory() {
        fetch("/api/inspection/list")
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    renderTableRows(data.records);
                    if (statusDb) statusDb.textContent = `💾 DATABASE: ${data.records.length} RECORDS`;
                }
            })
            .catch(err => console.error(err));
    }

    let currentInspectionRecords = [];

    function getCleanPhotoUrl(fotoPath) {
        if (!fotoPath) return DEFAULT_THUMB_SVG;
        let raw = String(fotoPath).split(';')[0].trim();
        if (!raw) return DEFAULT_THUMB_SVG;
        let filename = raw.replace(/\\/g, '/').split('/').pop();
        if (!filename) return DEFAULT_THUMB_SVG;
        return '/images/' + filename;
    }

    function updateSummaryCounters(records) {
        let total = records.length;
        let healthy = 0;
        let infected = 0;
        let pending = 0;

        records.forEach(r => {
            if (!r.uploaded) pending++;
            let h = r.tree_health_status || "TERTULAR_PARAH";
            if (h === "SEHAT") healthy++;
            else infected++;
        });

        setElemText("stat-total-count", total);
        setElemText("stat-healthy-count", healthy);
        setElemText("stat-infected-count", infected);
        setElemText("stat-pending-count", pending);
    }

    function renderTableRows(records) {
        if (!tableBody) return;
        tableBody.innerHTML = "";
        currentInspectionRecords = records || [];
        updateSummaryCounters(currentInspectionRecords);
        
        if (!records || records.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="10" class="empty-table-placeholder">Belum ada riwayat survei data tersimpan.</td></tr>`;
            return;
        }

        records.forEach(row => {
            const tr = document.createElement("tr");
            tr.style.cursor = "pointer";
            tr.dataset.rowId = row.id;
            const isUploaded = row.uploaded ? "SYNCHRONIZED" : "PENDING";
            const badgeClass = row.uploaded ? "uploaded" : "pending";
            const statusIcon = row.uploaded ? "🟢" : "🟡";
            const photoSrc = getCleanPhotoUrl(row.foto_path);

            let health = row.tree_health_status || "TERTULAR_PARAH";
            let healthBg = health === "SEHAT" ? "#10b981" : (health === "TERTULAR_ENGGA_PARAH" ? "#f59e0b" : "#ef4444");
            let healthText = health === "SEHAT" ? "🟢 SEHAT" : (health === "TERTULAR_ENGGA_PARAH" ? "🟡 RINGAN" : "🔴 PARAH");
            let nodeId = row.tree_node_id || "Pohon A";

            // Parse neighbors count
            let neighborCountInfo = "";
            try {
                if (row.spatial_compass_neighbors && row.spatial_compass_neighbors.startsWith("[")) {
                    let parsed = JSON.parse(row.spatial_compass_neighbors);
                    neighborCountInfo = ` (${parsed.length} Tetangga)`;
                }
            } catch (e) {}

            tr.innerHTML = `
                <td><input type="checkbox" class="chk-row" data-id="${row.id}" style="width:18px; height:18px; cursor:pointer;"></td>
                <td><strong style="font-family:'Space Grotesk',sans-serif; font-size:15px; font-weight:900;">#${row.id}</strong></td>
                <td>
                    <img src="${photoSrc}" alt="Foto" style="width:52px; height:52px; object-fit:cover; border-radius:6px; border:2.5px solid #000; box-shadow:2px 2px 0px #000; display:block;" onerror="this.onerror=null; this.src='${DEFAULT_THUMB_SVG}';">
                </td>
                <td>
                    <strong style="color:#0f172a; display:block; font-size:14px; font-weight:900;">${row.nama_perusahaan}</strong>
                    <span style="color:#334155; font-weight:800; font-size:12.5px; display:block; margin-top:2px;">${row.nama_kebun} ${row.afdeling ? '(' + row.afdeling + ')' : ''}</span>
                </td>
                <td><strong style="font-family:monospace; font-size:13.5px; font-weight:900; color:#0f172a;">${row.no_blok || '-'}</strong></td>
                <td>
                    <div style="display:flex; flex-wrap:wrap; gap:4px; font-size:11.5px; margin-bottom:4px;">
                        <span class="neo-badge bg-blue" style="padding:2px 6px; font-weight:900; border:1.5px solid #000; box-shadow:1px 1px 0px #000;">N:${row.nitrogen || 0}</span>
                        <span class="neo-badge" style="background:#a855f7; color:#000000; padding:2px 6px; font-weight:900; border:1.5px solid #000; box-shadow:1px 1px 0px #000;">P:${row.phosphor || 0}</span>
                        <span class="neo-badge bg-orange" style="padding:2px 6px; font-weight:900; border:1.5px solid #000; box-shadow:1px 1px 0px #000;">K:${row.kalium || 0}</span>
                        <span class="neo-badge bg-pink" style="padding:2px 6px; font-weight:900; border:1.5px solid #000; box-shadow:1px 1px 0px #000;">pH:${parseFloat(row.ph || 0).toFixed(1)}</span>
                        <span class="neo-badge bg-teal" style="padding:2px 6px; font-weight:900; border:1.5px solid #000; box-shadow:1px 1px 0px #000;">💧${parseFloat(row.moisture || 0).toFixed(1)}%</span>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:3px; font-size:10px;">
                        <span class="neo-badge" style="background:#38bdf8; color:#000; padding:1px 5px; font-weight:800; border:1px solid #000;" title="MQ-3 Alcohol">MQ3:${row.mq3_raw ?? 0}</span>
                        <span class="neo-badge" style="background:#22c55e; color:#000; padding:1px 5px; font-weight:800; border:1px solid #000;" title="MQ-135 Air Quality">MQ135:${row.mq135_raw ?? 0}</span>
                        <span class="neo-badge" style="background:#c084fc; color:#000; padding:1px 5px; font-weight:800; border:1px solid #000;" title="MQ-138 Benzene">MQ138:${row.mq138_raw ?? 0}</span>
                        <span class="neo-badge" style="background:#eab308; color:#000; padding:1px 5px; font-weight:800; border:1px solid #000;" title="TGS-2600 Air Contaminants">TGS2600:${row.tgs2600_raw ?? 0}</span>
                        <span class="neo-badge" style="background:#ec4899; color:#000; padding:1px 5px; font-weight:800; border:1px solid #000;" title="TGS-2602 VOC/Odor">TGS2602:${row.tgs2602_raw ?? 0}</span>
                    </div>
                </td>
                <td>
                    <div style="font-size:12px;">
                        <strong style="color:#6d28d9; font-weight:900; font-size:14px;">${nodeId}</strong>
                        <span class="neo-badge" style="background:${healthBg}; color:#fff; font-size:10.5px; padding:3px 8px; margin-left:4px; font-weight:900; border:1.5px solid #000;">${healthText}</span>
                        <span style="display:block; color:#334155; font-weight:800; font-size:11px; margin-top:3px;">${neighborCountInfo}</span>
                    </div>
                </td>
                <td><strong style="font-family:monospace; font-size:13px; font-weight:800; color:#0f172a;">${row.tanggal_pengambilan}</strong></td>
                <td><span class="status-lbl ${badgeClass}">${statusIcon} ${isUploaded}</span></td>
                <td>
                    <button type="button" class="neo-btn bg-teal btn-view-detail" data-row-id="${row.id}" style="font-size:11.5px; padding:6px 14px; font-weight:900; border:2.5px solid #000; box-shadow:2px 2px 0px #000;">🔍 DETAIL</button>
                </td>
            `;

            tableBody.appendChild(tr);
        });
    }

    // Search / Filter Event Listener
    const inputSearchHistory = document.getElementById("input-search-history");
    if (inputSearchHistory) {
        inputSearchHistory.addEventListener("input", (e) => {
            const q = e.target.value.toLowerCase().trim();
            if (!q) {
                renderTableRows(currentInspectionRecords);
                return;
            }
            const filtered = currentInspectionRecords.filter(r => {
                return (r.nama_perusahaan || '').toLowerCase().includes(q) ||
                       (r.nama_kebun || '').toLowerCase().includes(q) ||
                       (r.no_blok || '').toLowerCase().includes(q) ||
                       (r.tree_node_id || '').toLowerCase().includes(q) ||
                       (r.tanggal_pengambilan || '').toLowerCase().includes(q);
            });
            renderTableRows(filtered);
        });
    }

    // Export to CSV Function
    const btnExportCSV = document.getElementById("btn-export-csv");
    if (btnExportCSV) {
        btnExportCSV.addEventListener("click", () => {
            if (!currentInspectionRecords || currentInspectionRecords.length === 0) {
                alert("⚠️ Tidak ada data untuk diexport.");
                return;
            }
            let headers = ["ID", "Perusahaan", "Kebun", "Afdeling", "No Blok", "Tahun Tanam", "Luas Ha", "Terserang", "Tanggal", "Latitude", "Longitude", "N", "P", "K", "pH", "EC", "Moisture", "Temp", "MQ3_ADC", "MQ135_ADC", "MQ138_ADC", "TGS2600_ADC", "TGS2602_ADC", "Node ID", "Umur", "Health Status", "Tetangga Spasial"];
            let rows = currentInspectionRecords.map(r => [
                r.id,
                `"${r.nama_perusahaan || ''}"`,
                `"${r.nama_kebun || ''}"`,
                `"${r.afdeling || ''}"`,
                `"${r.no_blok || ''}"`,
                r.tahun_tanam || '',
                r.luas || '',
                r.jumlah_terserang || 0,
                r.tanggal_pengambilan || '',
                r.latitude || 0,
                r.longitude || 0,
                r.nitrogen || 0,
                r.phosphor || 0,
                r.kalium || 0,
                r.ph || 0,
                r.ec || 0,
                r.moisture || 0,
                r.temperature || 0,
                r.mq3_raw !== undefined ? r.mq3_raw : (r.mq3_adc || 0),
                r.mq135_raw !== undefined ? r.mq135_raw : (r.mq135_adc || 0),
                r.mq138_raw !== undefined ? r.mq138_raw : (r.mq138_adc || 0),
                r.tgs2600_raw !== undefined ? r.tgs2600_raw : (r.tgs2600_adc || 0),
                r.tgs2602_raw !== undefined ? r.tgs2602_raw : (r.tgs2602_adc || 0),
                `"${r.tree_node_id || ''}"`,
                r.tree_age || '',
                `"${r.tree_health_status || ''}"`,
                `"${(r.spatial_compass_neighbors || '').replace(/"/g, '""')}"`
            ]);

            let csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
            let encodedUri = encodeURI(csvContent);
            let link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `inspeksi_sawit_${new Date().toISOString().slice(0,10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    // Event delegation: klik DETAIL atau klik baris → buka modal detail
    if (tableBody) {
        tableBody.addEventListener("click", (e) => {
            if (e.target.type === "checkbox" || e.target.closest('input[type="checkbox"]')) return;

            const detailBtn = e.target.closest(".btn-view-detail");
            const tr = e.target.closest("tr");
            const rowId = detailBtn ? parseInt(detailBtn.dataset.rowId) : (tr ? parseInt(tr.dataset.rowId) : null);
            if (!rowId) return;

            const targetRow = currentInspectionRecords.find(r => r.id === rowId);
            if (targetRow) {
                openInspectionDetailModal(targetRow);
            } else {
                fetch("/api/inspection/list")
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.records) {
                            currentInspectionRecords = data.records;
                            const match = currentInspectionRecords.find(r => r.id === rowId);
                            if (match) openInspectionDetailModal(match);
                        }
                    });
            }
        });
    }

    function setElemText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function openInspectionDetailModal(row) {
        const modal = document.getElementById("modal-inspection-detail");
        if (!modal) return;
        
        setElemText("detail-modal-title", `DETAIL RECORD INSPEKSI #${row.id}`);
        
        const photoElem = document.getElementById("detail-photo-element");
        if (photoElem) {
            photoElem.src = getCleanPhotoUrl(row.foto_path);
        }

        setElemText("detail-corp-name", row.nama_perusahaan || '-');
        setElemText("detail-garden-name", `${row.nama_kebun || '-'} (Afdeling: ${row.afdeling || '-'})`);
        setElemText("detail-block-no", row.no_blok || '-');
        setElemText("detail-plant-year", row.tahun_tanam || '-');
        setElemText("detail-land-area", `${row.luas_lahan || row.luas || 0} Ha`);
        setElemText("detail-pest-count", `${row.jumlah_terserang || 0} Pohon`);
        setElemText("detail-timestamp", row.tanggal_pengambilan || row.timestamp || '-');
        
        const cloudStatusElem = document.getElementById("detail-cloud-status");
        if (cloudStatusElem) {
            cloudStatusElem.textContent = row.uploaded ? "SYNCHRONIZED (TERUNGGAH)" : "PENDING LOKAL";
            cloudStatusElem.style.color = row.uploaded ? "#00e087" : "#ffd700";
        }

        setElemText("detail-location-address", row.nama_lokasi || 'Alamat tidak tercatat');
        setElemText("detail-coords", `${parseFloat(row.latitude || 0).toFixed(6)}, ${parseFloat(row.longitude || 0).toFixed(6)}`);

        // NPK readings
        setElemText("detail-temp", `${parseFloat(row.temperature || 0).toFixed(1)} °C`);
        setElemText("detail-moisture", `${parseFloat(row.moisture || 0).toFixed(1)} %`);
        setElemText("detail-ph", `${parseFloat(row.ph || 0).toFixed(1)}`);
        setElemText("detail-ec", `${row.ec || 0} uS/cm`);
        setElemText("detail-n", `${row.nitrogen || 0} mg/kg`);
        setElemText("detail-p", `${row.phosphor || 0} mg/kg`);
        setElemText("detail-k", `${row.kalium || 0} mg/kg`);

        // Gas RAW ADC readings
        setElemText("detail-mq3", `${row.mq3_raw !== undefined ? row.mq3_raw : (row.mq3_adc || 0)} ADC`);
        setElemText("detail-mq135", `${row.mq135_raw !== undefined ? row.mq135_raw : (row.mq135_adc || 0)} ADC`);
        setElemText("detail-mq138", `${row.mq138_raw !== undefined ? row.mq138_raw : (row.mq138_adc || 0)} ADC`);
        setElemText("detail-tgs2600", `${row.tgs2600_raw !== undefined ? row.tgs2600_raw : (row.tgs2600_adc || 0)} ADC`);
        setElemText("detail-tgs2602", `${row.tgs2602_raw !== undefined ? row.tgs2602_raw : (row.tgs2602_adc || 0)} ADC`);

        // Tree Spatial Details
        setElemText("detail-tree-id", row.tree_node_id || 'Pohon A');
        setElemText("detail-tree-age", `${row.tree_age || 7} Tahun`);
        
        let health = row.tree_health_status || "TERTULAR_PARAH";
        let healthLabel = health === "SEHAT" ? "🟢 SEHAT" : (health === "TERTULAR_ENGGA_PARAH" ? "🟡 TERTULAR ENGGA PARAH" : "🔴 TERTULAR PARAH");
        setElemText("detail-tree-health", healthLabel);

        // Format neighbors
        const neighborsElem = document.getElementById("detail-tree-neighbors");
        if (neighborsElem) {
            let rawNeighbors = row.spatial_compass_neighbors || "";
            try {
                if (rawNeighbors.startsWith("[")) {
                    let parsed = JSON.parse(rawNeighbors);
                    neighborsElem.innerHTML = parsed.map((n, i) => {
                        let isTouch = n.touch === "TOUCHING";
                        let touchBadge = isTouch ? '<span style="color:#10b981; font-weight:bold;">🍃 DAUN BERSENTUHAN</span>' : '<span style="color:#94a3b8;">🚫 Terpisah</span>';
                        return `<div>• Tetangga #${i+1}: <strong>${n.treeId}</strong> (${n.deg}° | ${n.dist}m) - ${touchBadge}</div>`;
                    }).join("");
                } else {
                    neighborsElem.textContent = rawNeighbors || 'Tidak ada data tetangga.';
                }
            } catch (e) {
                neighborsElem.textContent = rawNeighbors || 'Tidak ada data tetangga.';
            }
        }

        modal.style.display = "flex";
    }

    if (btnCloseDetailModal) {
        btnCloseDetailModal.addEventListener("click", () => {
            if (modalInspectionDetail) modalInspectionDetail.style.display = "none";
        });
    }

    if (btnCloseDetailFooter) {
        btnCloseDetailFooter.addEventListener("click", () => {
            if (modalInspectionDetail) modalInspectionDetail.style.display = "none";
        });
    }

    if (modalInspectionDetail) {
        modalInspectionDetail.addEventListener("click", (e) => {
            if (e.target === modalInspectionDetail) {
                modalInspectionDetail.style.display = "none";
            }
        });
    }

    if (btnRefreshData) btnRefreshData.addEventListener("click", loadInspectionHistory);

    if (chkSelectAll) {
        chkSelectAll.addEventListener("change", () => {
            const checkboxes = document.querySelectorAll(".chk-row");
            checkboxes.forEach(chk => chk.checked = chkSelectAll.checked);
        });
    }

    function getCheckedIds() {
        const checkedBox = document.querySelectorAll(".chk-row:checked");
        const ids = [];
        checkedBox.forEach(chk => {
            ids.push(parseInt(chk.getAttribute("data-id")));
        });
        return ids;
    }

    if (btnDeleteSelected) {
        btnDeleteSelected.addEventListener("click", () => {
            const ids = getCheckedIds();
            if (ids.length === 0) {
                alert("Silakan centang baris tabel yang ingin dihapus.");
                return;
            }

            if (confirm(`Apakah Anda yakin ingin menghapus ${ids.length} data terpilih secara permanen?`)) {
                fetch("/api/inspection/delete", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ids: ids })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        loadInspectionHistory();
                    } else {
                        alert("Gagal menghapus data: " + data.message);
                    }
                });
            }
        });
    }

    if (btnUploadSelected) {
        btnUploadSelected.addEventListener("click", () => {
            const ids = getCheckedIds();
            if (ids.length === 0) {
                alert("Silakan centang baris tabel yang ingin diunggah ke cloud.");
                return;
            }

            btnUploadSelected.textContent = "⏳ UPLOADING...";
            btnUploadSelected.disabled = true;

            fetch("/api/inspection/upload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ids: ids })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                loadInspectionHistory();
            })
            .catch(err => {
                console.error(err);
                alert("Terjadi kegagalan upload data.");
            })
            .finally(() => {
                btnUploadSelected.textContent = "📤 UPLOAD TERPILIH";
                btnUploadSelected.disabled = false;
            });
        });
    }

    if (btnUploadAll) {
        btnUploadAll.addEventListener("click", () => {
            btnUploadAll.textContent = "⏳ UPLOADING ALL...";
            btnUploadAll.disabled = true;

            fetch("/api/inspection/upload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ all_pending: true })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                loadInspectionHistory();
            })
            .catch(err => {
                console.error(err);
                alert("Gagal upload semua pending.");
            })
            .finally(() => {
                btnUploadAll.textContent = "📤 UPLOAD SEMUA PENDING";
                btnUploadAll.disabled = false;
            });
        });
    }

    if (btnNewInspection) {
        btnNewInspection.addEventListener("click", () => {
            if (btnResetForm) btnResetForm.click();
            updateSensorGaugesDisplay({
                nitrogen: 0,
                phosphor: 0,
                kalium: 0,
                ph: 0.0,
                ec: 0,
                moisture: 0.0,
                temperature: 0.0
            });
            navigateToStep(0);
        });
    }

    // =============================================================================
    // GLOBAL SYSTEM STATES
    // =============================================================================
    
    let isUpdatingKiosk = false;
    function updateKioskStatus() {
        if (isUpdatingKiosk) return;
        isUpdatingKiosk = true;
        if (statusCam) statusCam.textContent = "📷 KIOSK CAMERA: LIVE ONLINE";
        
        fetchWithTimeout("/api/sensor/status", { timeout: 2500 })
            .then(res => res.json())
            .then(data => {
                const modeStatus = document.getElementById("mode-sensor-status");
                if (data.success && data.esp32_connected) {
                    if (modeStatus) {
                        modeStatus.textContent = "ESP32 PUSH ONLINE";
                        modeStatus.className = "mode-val text-green";
                    }
                    if (statusSensor) statusSensor.textContent = `🔌 SENSOR ENGINE: ESP32 ONLINE (${data.last_received})`;
                } else {
                    if (modeStatus) {
                        modeStatus.textContent = "MOCK SIMULATED";
                        modeStatus.className = "mode-val text-green";
                    }
                    if (statusSensor) statusSensor.textContent = "🔌 MODBUS ENGINE: READY";
                }
            })
            .catch(() => {})
            .finally(() => {
                isUpdatingKiosk = false;
            });
    }

    // Auto-update system status every 3 seconds
    setInterval(updateKioskStatus, 3000);

    // =============================================================================
    // STEPPER MOTOR PAN/TILT JOYSTICK (HOLD TO MOVE, RELEASE TO STOP)
    // =============================================================================
    const btnStepperDirs = document.querySelectorAll(".btn-stepper-dir");
    let activeStepperDir = null;
    let isSendingStepper = false;
    let pendingStepperCmd = null;

    function startStepperMove(dir, btnElement) {
        if (!dir || dir === "HOME") {
            stopStepperMove(btnElement);
            return;
        }
        activeStepperDir = dir;
        if (btnElement) {
            btnElement.style.opacity = "0.6";
            btnElement.style.filter = "brightness(1.4)";
        }

        if (isSendingStepper) {
            pendingStepperCmd = { type: "move", dir: dir, btnElement: btnElement };
            return;
        }
        isSendingStepper = true;

        fetchWithTimeout("/api/stepper/move", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ direction: dir, action: "start" }),
            timeout: 2000
        })
        .then(res => res.json())
        .then(data => console.log("[STEPPER START OK]", data))
        .catch(err => console.error("[STEPPER START ERR]", err))
        .finally(() => {
            isSendingStepper = false;
            if (pendingStepperCmd) {
                const p = pendingStepperCmd;
                pendingStepperCmd = null;
                if (p.type === "stop") stopStepperMove(p.btnElement);
                else if (p.type === "move") startStepperMove(p.dir, p.btnElement);
            }
        });
    }

    function stopStepperMove(btnElement) {
        activeStepperDir = null;
        if (btnElement) {
            btnElement.style.opacity = "1.0";
            btnElement.style.filter = "none";
        }

        if (isSendingStepper) {
            pendingStepperCmd = { type: "stop", btnElement: btnElement };
            return;
        }
        isSendingStepper = true;

        fetchWithTimeout("/api/stepper/stop", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "stop" }),
            timeout: 2000
        })
        .then(res => res.json())
        .then(data => console.log("[STEPPER STOP OK]", data))
        .catch(err => console.error("[STEPPER STOP ERR]", err))
        .finally(() => {
            isSendingStepper = false;
            if (pendingStepperCmd) {
                const p = pendingStepperCmd;
                pendingStepperCmd = null;
                if (p.type === "stop") stopStepperMove(p.btnElement);
                else if (p.type === "move") startStepperMove(p.dir, p.btnElement);
            }
        });
    }

    btnStepperDirs.forEach(btn => {
        const dir = btn.getAttribute("data-dir") || "";

        if (window.PointerEvent) {
            btn.addEventListener("pointerdown", (e) => {
                e.preventDefault();
                try { btn.setPointerCapture(e.pointerId); } catch(err) {}
                startStepperMove(dir, btn);
            });

            btn.addEventListener("pointerup", (e) => {
                e.preventDefault();
                try { btn.releasePointerCapture(e.pointerId); } catch(err) {}
                stopStepperMove(btn);
            });

            btn.addEventListener("pointercancel", (e) => {
                e.preventDefault();
                try { btn.releasePointerCapture(e.pointerId); } catch(err) {}
                stopStepperMove(btn);
            });
        } else {
            // Fallback for older devices without PointerEvent support
            btn.addEventListener("mousedown", (e) => { e.preventDefault(); startStepperMove(dir, btn); });
            btn.addEventListener("mouseup", (e) => { e.preventDefault(); stopStepperMove(btn); });
            btn.addEventListener("touchstart", (e) => { e.preventDefault(); startStepperMove(dir, btn); });
            btn.addEventListener("touchend", (e) => { e.preventDefault(); stopStepperMove(btn); });
            btn.addEventListener("touchcancel", (e) => { e.preventDefault(); stopStepperMove(btn); });
        }
    });
});
