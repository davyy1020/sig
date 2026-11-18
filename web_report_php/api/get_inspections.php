<?php
/**
 * API GET Inspections (PHP)
 * =========================
 * Mengambil daftar seluruh data inspeksi dari MySQL Server.
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../config.php';

try {
    $pdo = getDbConnection();
    
    $stmt = $pdo->query("SELECT * FROM inspections ORDER BY timestamp DESC");
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Cast numeric & integer fields for JSON output consistency
    foreach ($rows as &$row) {
        $row['id'] = intval($row['id']);
        $row['luas'] = floatval($row['luas']);
        $row['jumlah_terserang'] = intval($row['jumlah_terserang']);
        $row['latitude'] = floatval($row['latitude']);
        $row['longitude'] = floatval($row['longitude']);
        $row['nitrogen'] = floatval($row['nitrogen']);
        $row['phosphor'] = floatval($row['phosphor']);
        $row['kalium'] = floatval($row['kalium']);
        $row['ph'] = floatval($row['ph']);
        $row['ec'] = floatval($row['ec']);
        $row['moisture'] = floatval($row['moisture']);
        $row['temperature'] = floatval($row['temperature']);
        $row['uploaded'] = intval($row['uploaded']);
    }

    echo json_encode([
        "success" => true,
        "count"   => count($rows),
        "data"    => $rows
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "success" => false,
        "message" => "Error fetching data from MySQL: " . $e->getMessage()
    ]);
}
