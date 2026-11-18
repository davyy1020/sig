-- ====================================================
-- MySQL Database Schema untuk SIG Web Report (PHP)
-- ====================================================

CREATE DATABASE IF NOT EXISTS sig_monitoring 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

USE sig_monitoring;

CREATE TABLE IF NOT EXISTS inspections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_perusahaan VARCHAR(255),
    nama_kebun VARCHAR(255),
    afdeling VARCHAR(100),
    no_blok VARCHAR(100),
    tahun_tanam VARCHAR(50),
    luas DOUBLE,
    jumlah_terserang INT,
    tanggal_pengambilan VARCHAR(100),
    latitude DOUBLE,
    longitude DOUBLE,
    nama_lokasi VARCHAR(255),
    nitrogen DOUBLE,
    phosphor DOUBLE,
    kalium DOUBLE,
    ph DOUBLE,
    ec DOUBLE,
    moisture DOUBLE,
    temperature DOUBLE,
    foto_path TEXT,
    video_path TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    uploaded TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
