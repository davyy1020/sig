/* ====================================================
   Web Report Dashboard JS - Filters, Excel Export & Theme Switcher
   ==================================================== */

let allInspections = [];
let currentFilteredData = [];

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    fetchInspections();

    document.getElementById('btn-refresh').addEventListener('click', fetchInspections);
    document.getElementById('btn-export-excel').addEventListener('click', exportToExcel);
    document.getElementById('theme-select').addEventListener('change', (e) => setTheme(e.target.value));

    document.getElementById('search-input').addEventListener('input', applyFilters);
    document.getElementById('filter-company').addEventListener('change', applyFilters);
    document.getElementById('filter-date-from').addEventListener('change', applyFilters);
    document.getElementById('filter-date-to').addEventListener('change', applyFilters);
    document.getElementById('btn-reset-filters').addEventListener('click', resetFilters);

    document.getElementById('btn-close-modal').addEventListener('click', closeModal);
    document.getElementById('photo-modal').addEventListener('click', (e) => {
        if (e.target.id === 'photo-modal') closeModal();
    });
});

function initTheme() {
    const savedTheme = localStorage.getItem('sig_theme') || 'dark';
    setTheme(savedTheme);
    document.getElementById('theme-select').value = savedTheme;
}

function setTheme(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem('sig_theme', themeName);
}

async function fetchInspections() {
    try {
        const response = await fetch('/api/inspections');
        const result = await response.json();

        if (result.success) {
            allInspections = result.data;
            populateCompanyDropdown(allInspections);
            applyFilters();
        } else {
            console.error('Failed to fetch inspections:', result.message);
        }
    } catch (err) {
        console.error('Error fetching API:', err);
    }
}

function populateCompanyDropdown(data) {
    const select = document.getElementById('filter-company');
    const currentValue = select.value;
    
    const companies = [...new Set(data.map(item => item.nama_perusahaan).filter(Boolean))].sort();

    select.innerHTML = '<option value="">-- Semua Perusahaan --</option>';
    companies.forEach(company => {
        const opt = document.createElement('option');
        opt.value = company;
        opt.textContent = company;
        select.appendChild(opt);
    });

    select.value = currentValue;
}

function applyFilters() {
    const searchQuery = document.getElementById('search-input').value.toLowerCase().trim();
    const companyQuery = document.getElementById('filter-company').value;
    const dateFrom = document.getElementById('filter-date-from').value;
    const dateTo = document.getElementById('filter-date-to').value;

    currentFilteredData = allInspections.filter(item => {
        const matchesText = !searchQuery || (
            (item.nama_perusahaan && item.nama_perusahaan.toLowerCase().includes(searchQuery)) ||
            (item.nama_kebun && item.nama_kebun.toLowerCase().includes(searchQuery)) ||
            (item.no_blok && item.no_blok.toLowerCase().includes(searchQuery))
        );

        const matchesCompany = !companyQuery || item.nama_perusahaan === companyQuery;

        let matchesDate = true;
        if (item.tanggal_pengambilan || item.timestamp) {
            const itemDateStr = (item.tanggal_pengambilan || item.timestamp).substring(0, 10);
            if (dateFrom && itemDateStr < dateFrom) matchesDate = false;
            if (dateTo && itemDateStr > dateTo) matchesDate = false;
        }

        return matchesText && matchesCompany && matchesDate;
    });

    updateSummaryCards(currentFilteredData);
    renderTable(currentFilteredData);
}

function resetFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('filter-company').value = '';
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    applyFilters();
}

function updateSummaryCards(data) {
    document.getElementById('stat-total').innerText = data.length;

    const totalTerserang = data.reduce((acc, curr) => acc + (parseInt(curr.jumlah_terserang) || 0), 0);
    document.getElementById('stat-terserang').innerText = totalTerserang;

    let avgN = 0, avgP = 0, avgK = 0;
    if (data.length > 0) {
        avgN = (data.reduce((acc, curr) => acc + (parseFloat(curr.nitrogen) || 0), 0) / data.length).toFixed(1);
        avgP = (data.reduce((acc, curr) => acc + (parseFloat(curr.phosphor) || 0), 0) / data.length).toFixed(1);
        avgK = (data.reduce((acc, curr) => acc + (parseFloat(curr.kalium) || 0), 0) / data.length).toFixed(1);
    }
    document.getElementById('stat-npk').innerText = `${avgN} / ${avgP} / ${avgK}`;
}

function renderTable(data) {
    const tbody = document.getElementById('table-body');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 32px;">
                    Belum ada data inspeksi yang memenuhi kriteria filter.
                </td>
            </tr>
        `;
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');

        let photoHtml = `<div class="no-photo">📷</div>`;
        if (item.foto_path) {
            photoHtml = `<img src="${item.foto_path}" class="photo-thumb" alt="Foto Inspeksi" onclick="openModal(${item.id})">`;
        }

        const npkHtml = `
            <div class="npk-pills">
                <span class="npk-pill npk-n">N: ${item.nitrogen || 0}</span>
                <span class="npk-pill npk-p">P: ${item.phosphor || 0}</span>
                <span class="npk-pill npk-k">K: ${item.kalium || 0}</span>
            </div>
        `;

        const statusHtml = item.uploaded 
            ? `<span class="badge badge-uploaded">✅ Uploaded</span>` 
            : `<span class="badge badge-pending">⏳ Pending</span>`;

        tr.innerHTML = `
            <td>#${item.id}</td>
            <td>${photoHtml}</td>
            <td><strong>${escapeHtml(item.nama_perusahaan || '-')}</strong></td>
            <td>${escapeHtml(item.nama_kebun || '-')}</td>
            <td>Blok ${escapeHtml(item.no_blok || '-')}</td>
            <td>${npkHtml}</td>
            <td>${item.timestamp || '-'}</td>
            <td>${statusHtml}</td>
        `;

        tbody.appendChild(tr);
    });
}

function exportToExcel() {
    if (!currentFilteredData || currentFilteredData.length === 0) {
        alert('Tidak ada data inspeksi yang dapat diekspor.');
        return;
    }

    const hostUrl = window.location.origin;

    let excelHtml = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta charset="utf-8">
        <!--[if gte mso 9]>
        <xml>
            <x:ExcelWorkbook>
                <x:ExcelWorksheets>
                    <x:ExcelWorksheet>
                        <x:Name>Laporan Inspeksi Kebun</x:Name>
                        <x:WorksheetOptions>
                            <x:DisplayGridlines/>
                        </x:WorksheetOptions>
                    </x:ExcelWorksheet>
                </x:ExcelWorksheets>
            </x:ExcelWorkbook>
        </xml>
        <![endif]-->
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; }
            h2 { color: #107C41; }
            table { border-collapse: collapse; width: 100%; }
            th { background-color: #107C41; color: #FFFFFF; font-weight: bold; border: 1px solid #0E6B37; padding: 10px; text-align: center; }
            td { border: 1px solid #CBD5E1; padding: 8px; text-align: left; vertical-align: middle; }
            .num { text-align: right; }
            .center { text-align: center; }
            .badge-up { color: #10B981; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>🌿 LAPORAN DATA INSPEKSI PERKEBUNAN</h2>
        <p><b>Tanggal Ekspor:</b> ${new Date().toLocaleString('id-ID')}</p>
        <p><b>Total Data:</b> ${currentFilteredData.length} Inspeksi</p>
        <br>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Perusahaan</th>
                    <th>Nama Kebun</th>
                    <th>Afdeling</th>
                    <th>No Blok</th>
                    <th>Tahun Tanam</th>
                    <th>Luas (Ha)</th>
                    <th>Pohon Terserang</th>
                    <th>Tanggal Pengambilan</th>
                    <th>Latitude</th>
                    <th>Longitude</th>
                    <th>Nitrogen (N)</th>
                    <th>Phosphor (P)</th>
                    <th>Kalium (K)</th>
                    <th>pH</th>
                    <th>EC (µS/cm)</th>
                    <th>Moisture (%)</th>
                    <th>Temperature (°C)</th>
                    <th>Status Upload</th>
                    <th>Link Foto Server</th>
                </tr>
            </thead>
            <tbody>
    `;

    currentFilteredData.forEach(row => {
        const photoPath = row.foto_path || "";
        const fullPhotoUrl = photoPath ? (photoPath.startsWith('http') ? photoPath : hostUrl + photoPath) : "";

        excelHtml += `
            <tr>
                <td class="center">#${row.id || ""}</td>
                <td>${escapeHtml(row.nama_perusahaan || "")}</td>
                <td>${escapeHtml(row.nama_kebun || "")}</td>
                <td>${escapeHtml(row.afdeling || "")}</td>
                <td>${escapeHtml(row.no_blok || "")}</td>
                <td class="center">${escapeHtml(row.tahun_tanam || "")}</td>
                <td class="num">${row.luas || 0}</td>
                <td class="num">${row.jumlah_terserang || 0}</td>
                <td class="center">${escapeHtml(row.tanggal_pengambilan || row.timestamp || "")}</td>
                <td class="num">${row.latitude || 0}</td>
                <td class="num">${row.longitude || 0}</td>
                <td class="num">${row.nitrogen || 0}</td>
                <td class="num">${row.phosphor || 0}</td>
                <td class="num">${row.kalium || 0}</td>
                <td class="num">${row.ph || 0}</td>
                <td class="num">${row.ec || 0}</td>
                <td class="num">${row.moisture || 0}</td>
                <td class="num">${row.temperature || 0}</td>
                <td class="center badge-up">${row.uploaded ? "Uploaded" : "Pending"}</td>
                <td>${fullPhotoUrl ? `<a href="${fullPhotoUrl}" target="_blank">${fullPhotoUrl}</a>` : "-"}</td>
            </tr>
        `;
    });

    excelHtml += `
            </tbody>
        </table>
    </body>
    </html>
    `;

    const blob = new Blob([excelHtml], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    
    const now = new Date();
    const dateStr = now.getFullYear() +
        String(now.getMonth() + 1).padStart(2, '0') +
        String(now.getDate()).padStart(2, '0') + "_" +
        String(now.getHours()).padStart(2, '0') +
        String(now.getMinutes()).padStart(2, '0');
    
    const fileName = `Laporan_Inspeksi_Kebun_${dateStr}.xls`;

    const downloadLink = document.createElement("a");
    downloadLink.href = URL.createObjectURL(blob);
    downloadLink.download = fileName;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    
    setTimeout(() => URL.revokeObjectURL(downloadLink.href), 1000);
}

function openModal(id) {
    const item = allInspections.find(i => i.id === id);
    if (!item) return;

    document.getElementById('modal-img').src = item.foto_path || '';
    document.getElementById('modal-title').innerText = `Detail Inspeksi #${item.id} - ${item.nama_kebun || 'Kebun'}`;
    
    document.getElementById('m-perusahaan').innerText = item.nama_perusahaan || '-';
    document.getElementById('m-kebun').innerText = item.nama_kebun || '-';
    document.getElementById('m-blok').innerText = item.no_blok || '-';
    document.getElementById('m-npk').innerText = `N: ${item.nitrogen || 0} | P: ${item.phosphor || 0} | K: ${item.kalium || 0} mg/kg`;
    document.getElementById('m-ph-ec').innerText = `pH: ${item.ph || 0} | EC: ${item.ec || 0} µS/cm`;
    document.getElementById('m-moist-temp').innerText = `Moisture: ${item.moisture || 0}% | Temp: ${item.temperature || 0}°C`;
    document.getElementById('m-terserang').innerText = `${item.jumlah_terserang || 0} Pohon`;
    document.getElementById('m-timestamp').innerText = item.timestamp || '-';

    document.getElementById('photo-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('photo-modal').style.display = 'none';
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
