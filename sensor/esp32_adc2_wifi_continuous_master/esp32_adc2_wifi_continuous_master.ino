/*
 * ESP32 Continuous WiFi Master (RAW ADC Gas Readings + WiFi Continuous Push)
 * ===========================================================================
 * FITUR UTAMA:
 * - WiFi TETAP AKTIF TERUS (Continuous / Always Connected) TANPA WIFI_OFF.
 * - Menggunakan driver ADC2 baru (esp_adc/adc_oneshot.h) dengan retry loop
 *   agar GPIO 25 (TGS2600) & GPIO 27 (TGS2602) dapat dibaca aman saat WiFi aktif.
 * - Mengirim data RAW ADC (0 - 4095) + NPK Modbus RS485.
 * - Dual Transmission: Hardware Serial (Pin 4 & 2) + Wi-Fi HTTP Push ke Jetson Nano.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <HardwareSerial.h>
#include <ArduinoJson.h>
#include <math.h>
#include "esp_adc/adc_oneshot.h"

// ════════════════════════════════════════════════════════════════
//  KONFIGURASI UTAMA
// ════════════════════════════════════════════════════════════════

// WiFi Credentials
const char* WIFI_SSID     = "SIGMA";
const char* WIFI_PASSWORD = "sigma123";

// Static IP ESP32 & Target Jetson Nano
IPAddress ESP32_STATIC_IP(192, 168, 136, 145);
IPAddress GATEWAY_IP    (192, 168, 136, 1);
IPAddress SUBNET_MASK   (255, 255, 255, 0);
IPAddress DNS_SERVER    (8, 8, 8, 8);

const char* SENSOR_PUSH_URL = "http://192.168.136.138:5000/api/sensor/push";
const unsigned long READ_INTERVAL_MS = 3000;

// Pin Hardware Serial1 ke Jetson Nano Header J41
#define JETSON_UART_BAUD 115200
#define ESP_RX_PIN 4  // GPIO 4 (RX)  --> Jetson Pin 8 TX
#define ESP_TX_PIN 2  // GPIO 2 (TX)  --> Jetson Pin 10 RX

// Pin Hardware Serial2 ke NPK Modbus RS485
#define NPK_RX_PIN 17  // GPIO 17 (RO RS485)
#define NPK_TX_PIN 16  // GPIO 16 (DI RS485)
#define NPK_BAUD   9600
#define SLAVE_ID   0x01

// Pin Analog Gas Sensor Array (E-Nose)
#define PIN_A_MQ3     36 // ADC1
#define PIN_A_MQ135   35 // ADC1
#define PIN_A_MQ138   33 // ADC1
#define PIN_A_TGS2600 25 // ADC2 - retry reader
#define PIN_A_TGS2602 27 // ADC2 - retry reader

#define STATUS_LED_PIN 2

HardwareSerial SerialJetson(1);
HardwareSerial SerialNPK(2);

// Query Frame Modbus 8 Register
uint8_t npkQueryFrame[8] = { SLAVE_ID, 0x03, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00 };

struct SensorData {
  float temp = 0.0;
  float moisture = 0.0;
  uint16_t ec = 0;
  float ph = 0.0;
  uint16_t n = 0;
  uint16_t p = 0;
  uint16_t k = 0;

  int mq3_raw = 0;
  int mq135_raw = 0;
  int mq138_raw = 0;
  int tgs2600_raw = 0;
  int tgs2602_raw = 0;
};

SensorData currentData;
unsigned long lastSendTime = 0;

uint16_t calculateCRC16(const uint8_t* data, int length) {
  uint16_t crc = 0xFFFF;
  for (int pos = 0; pos < length; pos++) {
    crc ^= (uint16_t)data[pos];
    for (int i = 8; i != 0; i--) {
      if ((crc & 0x0001) != 0) {
        crc >>= 1;
        crc ^= 0xA001;
      } else {
        crc >>= 1;
      }
    }
  }
  return crc;
}

// ════════════════════════════════════════════════════════════════
//  FUNGSI MODBUS NPK RS485
// ════════════════════════════════════════════════════════════════

bool readPhysicalNPKSensor(SensorData& data) {
  while (SerialNPK.available() > 0) SerialNPK.read();

  Serial.println("\n------------------------------------------------------------------");
  Serial.print("📤 [NPK RS485 TX SEND] : ");
  for (int i = 0; i < 8; i++) Serial.printf("0x%02X ", npkQueryFrame[i]);
  Serial.println();

  SerialNPK.write(npkQueryFrame, 8);
  SerialNPK.flush();

  uint8_t response[32];
  int bytesRead = 0;
  unsigned long startTimeout = millis();

  while ((millis() - startTimeout < 1000) && (bytesRead < 32)) {
    if (SerialNPK.available() > 0) {
      response[bytesRead++] = SerialNPK.read();
    }
  }

  Serial.printf("📥 [NPK RS485 RX RECV] : %d Bytes Diterima\n", bytesRead);
  if (bytesRead < 7) return false;

  if (response[0] != SLAVE_ID || response[1] != 0x03) return false;

  uint16_t calcCrc = calculateCRC16(response, bytesRead - 2);
  uint16_t recvCrc = response[bytesRead - 2] | (response[bytesRead - 1] << 8);

  if (calcCrc != recvCrc) return false;

  uint16_t moist_raw = (response[3] << 8) | response[4];
  int16_t temp_raw  = (response[5] << 8) | response[6];
  uint16_t ec_raw    = (response[7] << 8) | response[8];
  uint16_t ph_raw    = (response[9] << 8) | response[10];
  uint16_t n_raw     = (response[11] << 8) | response[12];
  uint16_t p_raw     = (response[13] << 8) | response[14];
  uint16_t k_raw     = (response[15] << 8) | response[16];

  data.moisture = moist_raw / 10.0;
  data.temp     = temp_raw / 10.0;
  data.ec       = ec_raw;
  data.ph       = ph_raw / 10.0;
  data.n        = n_raw;
  data.p        = p_raw;
  data.k        = k_raw;

  Serial.println("🌱 [HASIL BACAAN NPK]:");
  Serial.printf("   - Suhu       : %.1f °C\n", data.temp);
  Serial.printf("   - Kelembaban : %.1f %%\n", data.moisture);
  Serial.printf("   - pH         : %.1f\n", data.ph);
  Serial.printf("   - EC         : %d uS/cm\n", data.ec);
  Serial.printf("   - Nitrogen   : %d mg/kg\n", data.n);
  Serial.printf("   - Fosfor     : %d mg/kg\n", data.p);
  Serial.printf("   - Kalium     : %d mg/kg\n", data.k);
  Serial.println("------------------------------------------------------------------");
  return true;
}

// ════════════════════════════════════════════════════════════════
//  DRIVER ADC2 (oneshot retry reader - WiFi Tetap Nyala)
// ════════════════════════════════════════════════════════════════

adc_channel_t getADC2Channel(int pin) {
  switch (pin) {
    case 25: return ADC_CHANNEL_8;
    case 27: return ADC_CHANNEL_7;
    case 14: return ADC_CHANNEL_6;
    case 12: return ADC_CHANNEL_5;
    case 13: return ADC_CHANNEL_4;
    case 15: return ADC_CHANNEL_3;
    case 2:  return ADC_CHANNEL_2;
    case 0:  return ADC_CHANNEL_1;
    case 4:  return ADC_CHANNEL_0;
    default: return ADC_CHANNEL_8;
  }
}

adc_oneshot_unit_handle_t adc2_handle = NULL;

void initADC2Driver() {
  adc_oneshot_unit_init_cfg_t init_config2 = {};
  init_config2.unit_id = ADC_UNIT_2;
  init_config2.ulp_mode = ADC_ULP_MODE_DISABLE;

  esp_err_t r = adc_oneshot_new_unit(&init_config2, &adc2_handle);
  if (r != ESP_OK) {
    Serial.printf("❌ Gagal init driver ADC2 (err=%d)\n", r);
    adc2_handle = NULL;
    return;
  }

  adc_oneshot_chan_cfg_t chan_config = {};
  chan_config.bitwidth = ADC_BITWIDTH_DEFAULT;
  chan_config.atten = ADC_ATTEN_DB_11;

  adc_channel_t ch2600 = getADC2Channel(PIN_A_TGS2600);
  adc_channel_t ch2602 = getADC2Channel(PIN_A_TGS2602);

  adc_oneshot_config_channel(adc2_handle, ch2600, &chan_config);
  adc_oneshot_config_channel(adc2_handle, ch2602, &chan_config);

  Serial.println("✅ Driver ADC2 (adc_oneshot) siap.");
}

int readADC2WithRetry(int pin, int maxRetry = 8) {
  if (adc2_handle == NULL) return -1;

  adc_channel_t channel = getADC2Channel(pin);
  int raw = 0;
  esp_err_t r;

  for (int attempt = 0; attempt < maxRetry; attempt++) {
    r = adc_oneshot_read(adc2_handle, channel, &raw);
    if (r == ESP_OK) return raw;
    delayMicroseconds(500); // Tunggu window kosong dari WiFi driver
  }
  return -1;
}

int readStableADC2(int pin) {
  long sum = 0;
  int validCount = 0;

  for (int i = 0; i < 16; i++) {
    int val = readADC2WithRetry(pin, 5);
    if (val >= 0) {
      sum += val;
      validCount++;
    }
    delayMicroseconds(200);
  }
  if (validCount == 0) return -1;
  return (int)(sum / validCount);
}

int readStableADC(int pin) {
  long sum = 0;
  for (int i = 0; i < 16; i++) {
    sum += analogRead(pin);
    delayMicroseconds(200);
  }
  return (int)(sum / 16);
}

void readGasSensorsRaw(SensorData& data) {
  // ADC1 (GPIO 36, 35, 33) - Bebas dari WiFi
  data.mq3_raw   = readStableADC(PIN_A_MQ3);
  data.mq135_raw = readStableADC(PIN_A_MQ135);
  data.mq138_raw = readStableADC(PIN_A_MQ138);

  // ADC2 (GPIO 25, 27) - Read with oneshot retry driver (WiFi TETAP NYALA)
  int tgs2600_val = readStableADC2(PIN_A_TGS2600);
  int tgs2602_val = readStableADC2(PIN_A_TGS2602);

  if (tgs2600_val >= 0) {
    data.tgs2600_raw = tgs2600_val;
  } else {
    Serial.println("⚠️ TGS2600 (ADC2) Retry Timeout. Mempertahankan nilai RAW sebelumnya.");
  }

  if (tgs2602_val >= 0) {
    data.tgs2602_raw = tgs2602_val;
  } else {
    Serial.println("⚠️ TGS2602 (ADC2) Retry Timeout. Mempertahankan nilai RAW sebelumnya.");
  }

  Serial.println("📡 [HASIL RAW DATA SENSOR GAS (0-4095)]:");
  Serial.printf("   - MQ-3     (GPIO 36) : RAW ADC %4d (%.2f V)\n", data.mq3_raw, (data.mq3_raw / 4095.0) * 3.3);
  Serial.printf("   - MQ-135   (GPIO 35) : RAW ADC %4d (%.2f V)\n", data.mq135_raw, (data.mq135_raw / 4095.0) * 3.3);
  Serial.printf("   - MQ-138   (GPIO 33) : RAW ADC %4d (%.2f V)\n", data.mq138_raw, (data.mq138_raw / 4095.0) * 3.3);
  Serial.printf("   - TGS-2600 (GPIO 25) : RAW ADC %4d (%.2f V)\n", data.tgs2600_raw, (data.tgs2600_raw / 4095.0) * 3.3);
  Serial.printf("   - TGS-2602 (GPIO 27) : RAW ADC %4d (%.2f V)\n", data.tgs2602_raw, (data.tgs2602_raw / 4095.0) * 3.3);
}

// ════════════════════════════════════════════════════════════════
//  WIFI CONTINUOUS MANAGEMENT
// ════════════════════════════════════════════════════════════════

void connectWiFiStaticAsync() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.config(ESP32_STATIC_IP, GATEWAY_IP, SUBNET_MASK, DNS_SERVER);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED_PIN, OUTPUT);
  
  // Set ADC 12-bit resolution & 11dB attenuation (Full 0 - 3.3V range for ESP32 Core v3.0.7)
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  analogSetPinAttenuation(PIN_A_MQ3, ADC_11db);
  analogSetPinAttenuation(PIN_A_MQ135, ADC_11db);
  analogSetPinAttenuation(PIN_A_MQ138, ADC_11db);

  SerialJetson.begin(JETSON_UART_BAUD, SERIAL_8N1, ESP_RX_PIN, ESP_TX_PIN);
  SerialNPK.begin(NPK_BAUD, SERIAL_8N1, NPK_RX_PIN, NPK_TX_PIN);

  uint16_t crc = calculateCRC16(npkQueryFrame, 6);
  npkQueryFrame[6] = crc & 0xFF;
  npkQueryFrame[7] = (crc >> 8) & 0xFF;

  // Inisialisasi Driver ADC2 Oneshot Retry Reader
  initADC2Driver();

  // Koneksi Wi-Fi awal (Background Continuous)
  connectWiFiStaticAsync();
  Serial.println("🚀 [ESP32 HYBRID MASTER] Ready! WiFi Continuous + RAW ADC Oneshot Retry.");
}

void loop() {
  unsigned long now = millis();
  
  // Wi-Fi Auto Reconnect jika terputus di background
  connectWiFiStaticAsync();

  if (now - lastSendTime >= READ_INTERVAL_MS) {
    lastSendTime = now;

    bool readOk = readPhysicalNPKSensor(currentData);
    if (!readOk) {
      currentData.temp = 0.0;
      currentData.moisture = 0.0;
      currentData.ph = 0.0;
      currentData.ec = 0;
      currentData.n = 0;
      currentData.p = 0;
      currentData.k = 0;
    }
    
    // Baca RAW ADC (Wi-Fi TETAP AKTIF DAN CONNECTED)
    readGasSensorsRaw(currentData);

    // Build JSON Payload
    JsonDocument doc;
    doc["nitrogen"]    = currentData.n;
    doc["phosphor"]    = currentData.p;
    doc["kalium"]      = currentData.k;
    doc["ph"]          = serialized(String(currentData.ph, 2));
    doc["ec"]          = currentData.ec;
    doc["moisture"]    = serialized(String(currentData.moisture, 1));
    doc["temperature"] = serialized(String(currentData.temp, 1));

    // Kirim RAW ADC gas sensor (0 - 4095)
    doc["mq3_raw"]     = currentData.mq3_raw;
    doc["mq135_raw"]   = currentData.mq135_raw;
    doc["mq138_raw"]   = currentData.mq138_raw;
    doc["tgs2600_raw"] = currentData.tgs2600_raw;
    doc["tgs2602_raw"] = currentData.tgs2602_raw;

    doc["mq3_adc"]     = currentData.mq3_raw;
    doc["mq135_adc"]   = currentData.mq135_raw;
    doc["mq138_adc"]   = currentData.mq138_raw;
    doc["tgs2600_adc"] = currentData.tgs2600_raw;
    doc["tgs2602_adc"] = currentData.tgs2602_raw;

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    // 1. Transmisi Serial UART ke Jetson Nano (Pin 2 & 4)
    SerialJetson.println(jsonPayload);
    Serial.println("[SERIAL TX Pin 2] -> " + jsonPayload);

    // 2. Transmisi Wi-Fi HTTP Push (Wi-Fi Tetap Connect)
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(SENSOR_PUSH_URL);
      http.addHeader("Content-Type", "application/json");
      http.setTimeout(3000);
      int code = http.POST(jsonPayload);
      if (code == 200) {
        digitalWrite(STATUS_LED_PIN, HIGH);
        Serial.println("🌐 [HTTP PUSH 200 OK] Data berhasil di-push ke Jetson Nano!");
      } else {
        digitalWrite(STATUS_LED_PIN, LOW);
        Serial.printf("⚠️ [HTTP PUSH ERROR] HTTP Code: %d\n", code);
      }
      http.end();
    }
  }
}
