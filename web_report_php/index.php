<!DOCTYPE html>
<html lang="id" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌿 SIG Web Report - Monitoring Kebun & Laporan</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/css/style.css">
</head>
<body>

    <!-- Header Navbar -->
    <header class="navbar">
        <div class="brand">
            <span class="brand-icon">🌿</span>
            <span class="brand-title">SIG Monitoring Kebun - Web Report</span>
        </div>
        <div class="nav-actions">
            <!-- Selector Tema -->
            <select id="theme-select" class="select-control" title="Pilih Tema Tampilan">
                <option value="dark">🌙 Dark Emerald</option>
                <option value="light">☀️ Light Fresh</option>
                <option value="navy">🌌 Cyber Navy</option>
            </select>

            <!-- Tombol Ekspor Excel -->
            <button id="btn-export-excel" class="btn btn-excel" title="Download Laporan ke File Excel (.csv/.xlsx)">
                <span>📊</span> Ekspor Excel
            </button>

            <!-- Tombol Refresh -->
            <button id="btn-refresh" class="btn btn-refresh">
                <span>🔄</span> Refresh
            </button>
        </div>
    </header>

    <!-- Main Container -->
    <main class="container">
        
        <!-- Stats Summary Cards -->
        <section class="stats-grid">
            <div class="stat-card card-green">
                <span class="stat-label">Total Inspeksi</span>
                <span id="stat-total" class="stat-value">0</span>
                <span class="stat-desc">Data tersimpan di database MySQL</span>
            </div>
            <div class="stat-card card-yellow">
                <span class="stat-label">Pohon Terserang</span>
                <span id="stat-terserang" class="stat-value">0</span>
                <span class="stat-desc">Total pohon butuh perawatan</span>
            </div>
            <div class="stat-card card-red">
                <span class="stat-label">Rata-Rata N / P / K</span>
                <span id="stat-npk" class="stat-value">0 / 0 / 0</span>
                <span class="stat-desc">Kadar nutrisi tanah (mg/kg)</span>
            </div>
        </section>

        <!-- Section Controls & Filter Lanjutan -->
        <section class="controls-bar">
            <div class="filter-group">
                <!-- Search Input -->
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="search-input" class="search-input" placeholder="Cari Perusahaan, Kebun, atau Blok...">
                </div>

                <!-- Filter Perusahaan -->
                <select id="filter-company" class="select-control">
                    <option value="">-- Semua Perusahaan --</option>
                </select>

                <!-- Filter Date Range -->
                <div class="date-filter-box">
                    <span>Dari:</span>
                    <input type="date" id="filter-date-from" class="input-control">
                    <span>Sampai:</span>
                    <input type="date" id="filter-date-to" class="input-control">
                </div>

                <!-- Reset Filter -->
                <button id="btn-reset-filters" class="btn btn-ghost" title="Reset Semua Filter">
                    ✖ Reset Filter
                </button>
            </div>
        </section>

        <!-- Data Table Card -->
        <section class="table-card">
            <div class="table-responsive">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Foto</th>
                            <th>Perusahaan</th>
                            <th>Nama Kebun</th>
                            <th>Blok</th>
                            <th>Kadar NPK</th>
                            <th>Tanggal Pengambilan</th>
                            <th>Status Upload</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Content loaded dynamically via JavaScript -->
                    </tbody>
                </table>
            </div>
        </section>

    </main>

    <!-- Modal Lightbox Viewer Foto & Detail -->
    <div id="photo-modal" class="modal-overlay">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modal-title" class="modal-title">Detail Inspeksi</h3>
                <button id="btn-close-modal" class="btn-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="modal-image-container">
                    <img id="modal-img" src="" alt="Foto Ukuran Penuh" class="modal-img">
                </div>
                <div class="modal-details">
                    <div class="detail-row">
                        <span class="detail-label">Perusahaan</span>
                        <span id="m-perusahaan" class="detail-value">-</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Nama Kebun</span>
                        <span id="m-kebun" class="detail-value">-</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">No. Blok</span>
                        <span id="m-blok" class="detail-value">-</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Nutrisi (NPK)</span>
                        <span id="m-npk" class="detail-value">-</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">pH & EC</span>
                        <span id="m-ph-ec" class="detail-value">-</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Moisture & Temp</span>
                        <span id="m-moist-temp" class="detail-value">-</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Jumlah Terserang</span>
                        <span id="m-terserang" class="detail-value">-</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Waktu Pengambilan</span>
                        <span id="m-timestamp" class="detail-value">-</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="static/js/report.js"></script>
</body>
</html>
