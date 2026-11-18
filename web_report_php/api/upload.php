<?php
/**
 * API Receiver Upload (PHP)
 * =========================
 * Menerima HTTP POST Multipart:
 * - json_data : Data inspeksi dalam format JSON string
 * - photo     : File foto inspeksi (opsional)
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(["success" => false, "message" => "Method Not Allowed. Gunakan HTTP POST."]);
    exit;
}

require_once __DIR__ . '/../config.php';

try {
    // 1. Ambil data JSON dari form parameter 'json_data'
    $rawJson = $_POST['json_data'] ?? '{}';
    $data = json_decode($rawJson, true);

    if (!is_array($data)) {
        $data = [];
    }

    // 2. Folder Upload Foto
    $uploadDir = __DIR__ . '/../uploads/photos/';
    if (!file_exists($uploadDir)) {
        mkdir($uploadDir, 0777, true);
    }

    $photoUrl = $data['foto_path'] ?? '';

    // 3. Proses File Foto jika diunggah via multipart 'photo'
    if (isset($_FILES['photo']) && $_FILES['photo']['error'] === UPLOAD_ERR_OK) {
        $fileTmpPath = $_FILES['photo']['tmp_name'];
        $fileName = basename($_FILES['photo']['name']);
        $fileExtension = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));

        $allowedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp'];
        if (in_array($fileExtension, $allowedExtensions)) {
            $timestampStr = date('Ymd_His');
            $newFileName = $timestampStr . '_' . preg_replace('/[^a-zA-Z0-9_\.-]/', '_', $fileName);
            $destPath = $uploadDir . $newFileName;

            if (move_uploaded_file($fileTmpPath, $destPath)) {
                $photoUrl = 'uploads/photos/' . $newFileName;
                $data['foto_path'] = $photoUrl;
            }
        }
    }

    // 4. Koneksi ke MySQL
    $pdo = getDbConnection();

    // 5. Query INSERT data ke MySQL
    $sql = "INSERT INTO inspections (
        nama_perusahaan, nama_kebun, afdeling, no_blok, tahun_tanam, luas, 
        jumlah_terserang, tanggal_pengambilan, latitude, longitude, nama_lokasi, 
        nitrogen, phosphor, kalium, ph, ec, moisture, temperature, foto_path, video_path, timestamp, uploaded
    ) VALUES (
        :nama_perusahaan, :nama_kebun, :afdeling, :no_blok, :tahun_tanam, :luas, 
        :jumlah_terserang, :tanggal_pengambilan, :latitude, :longitude, :nama_lokasi, 
        :nitrogen, :phosphor, :kalium, :ph, :ec, :moisture, :temperature, :foto_path, :video_path, :timestamp, 1
    )";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([
        ':nama_perusahaan'     => $data['nama_perusahaan'] ?? '',
        ':nama_kebun'          => $data['nama_kebun'] ?? '',
        ':afdeling'            => $data['afdeling'] ?? '',
        ':no_blok'             => $data['no_blok'] ?? '',
        ':tahun_tanam'         => $data['tahun_tanam'] ?? '',
        ':luas'                => floatval($data['luas'] ?? 0),
        ':jumlah_terserang'    => intval($data['jumlah_terserang'] ?? 0),
        ':tanggal_pengambilan' => $data['tanggal_pengambilan'] ?? date('Y-m-d'),
        ':latitude'            => floatval($data['latitude'] ?? 0),
        ':longitude'           => floatval($data['longitude'] ?? 0),
        ':nama_lokasi'         => $data['nama_lokasi'] ?? '',
        ':nitrogen'            => floatval($data['nitrogen'] ?? 0),
        ':phosphor'            => floatval($data['phosphor'] ?? 0),
        ':kalium'              => floatval($data['kalium'] ?? 0),
        ':ph'                  => floatval($data['ph'] ?? 0),
        ':ec'                  => floatval($data['ec'] ?? 0),
        ':moisture'            => floatval($data['moisture'] ?? 0),
        ':temperature'         => floatval($data['temperature'] ?? 0),
        ':foto_path'           => $data['foto_path'] ?? '',
        ':video_path'          => $data['video_path'] ?? '',
        ':timestamp'           => $data['timestamp'] ?? date('Y-m-d H:i:s')
    ]);

    $insertedId = $pdo->lastInsertId();

    http_response_code(201);
    echo json_encode([
        "success"  => true,
        "message"  => "Data inspeksi & foto berhasil diterima dan disimpan di MySQL Server (PHP)!",
        "id"       => (int)$insertedId,
        "foto_url" => $photoUrl
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "success" => false,
        "message" => "Server Error PHP: " . $e->getMessage()
    ]);
}
