<?php
/**
 * Konfigurasi Database MySQL & Helper Koneksi PDO
 * ===============================================
 */

define('DB_HOST', '127.0.0.1');
define('DB_PORT', 3306);
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_NAME', 'sig_monitoring');

/**
 * Mendapatkan koneksi PDO ke MySQL Server.
 * Otomatis membuat database & tabel 'inspections' jika belum ada.
 */
function getDbConnection() {
    try {
        // 1. Koneksi tanpa spesifikasi database untuk membuat database jika belum ada
        $dsnNoDb = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";charset=utf8mb4";
        $pdoNoDb = new PDO($dsnNoDb, DB_USER, DB_PASS, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
        ]);
        
        $dbName = DB_NAME;
        $pdoNoDb->exec("CREATE DATABASE IF NOT EXISTS `$dbName` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
        
        // 2. Koneksi ke database yang sudah dibuat
        $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
        $pdo = new PDO($dsn, DB_USER, DB_PASS, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
        ]);

        // 3. Pastikan tabel 'inspections' sudah dibuat
        createInspectionsTable($pdo);

        return $pdo;
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode([
            "success" => false,
            "message" => "Database Connection Error: " . $e->getMessage()
        ]);
        exit;
    }
}

/**
 * Otomatis membuat tabel 'inspections' jika belum ada.
 */
function createInspectionsTable($pdo) {
    $sql = "
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
    ";
    $pdo->exec($sql);
}
