/*
 * Arduino CNC Shield v3.0 - WEB GIMBAL STEPPER CONTROL (HOLD TO MOVE, RELEASE TO STOP)
 * ===================================================================================
 * Hardware Target : Arduino Uno / Nano + CNC Shield v3.0
 * Terhubung ke    : NVIDIA Jetson Nano / PC via Kabel USB Serial (Baudrate 115200)
 *
 * PEMETAAN SUMBU:
 *  - MOTOR Y (Slot C2 - D3/D6) : KANAN ('YR') & KIRI ('YL')
 *  - MOTOR X (Slot C1 - D2/D5) : ATAS  ('XU') & BAWAH ('XD')
 *  - STOP                    : RELEASE TOMBOL ('S')
 */

#include <AccelStepper.h>

#define ENABLE_PIN 8 // Shared Enable Pin D8 (Active LOW)

// Pin Driver Mapping
#define X_STEP 2
#define X_DIR  5
#define Y_STEP 3
#define Y_DIR  6

#define STEPPER_SPEED 400.0 // Kecepatan kontinu ideal untuk A4988/CNC Shield (tanpa stall)

AccelStepper stepperX(AccelStepper::DRIVER, X_STEP, X_DIR);
AccelStepper stepperY(AccelStepper::DRIVER, Y_STEP, Y_DIR);

enum MoveState {
  IDLE,
  MOVE_Y_RIGHT, // KANAN
  MOVE_Y_LEFT,  // KIRI
  MOVE_X_UP,    // ATAS
  MOVE_X_DOWN   // BAWAH
};

MoveState currentState = IDLE;
unsigned long lastCommandTime = 0;
const unsigned long SAFETY_TIMEOUT_MS = 400; // Auto-stop jika jaringan disconnect > 400ms

void setup() {
  Serial.begin(115200); // High speed serial UART ke Jetson Nano
  Serial.setTimeout(50);

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // LOW = Power ON terus ke driver

  stepperX.setMaxSpeed(1000.0);
  stepperY.setMaxSpeed(1000.0);

  Serial.println(F("OK: ARDUINO CNC SHIELD WEB GIMBAL READY"));
}

void loop() {
  // 1. Baca Perintah Serial dari Jetson Nano (Python Web App)
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.length() > 0) {
      lastCommandTime = millis(); // Refresh watchdog timer

      if (cmd == "YR") { // KANAN
        if (currentState != MOVE_Y_RIGHT) Serial.println(F("ACK: YR"));
        currentState = MOVE_Y_RIGHT;
        
        stepperY.setSpeed(STEPPER_SPEED);
      } 
      else if (cmd == "YL") { // KIRI
        if (currentState != MOVE_Y_LEFT) Serial.println(F("ACK: YL"));
        currentState = MOVE_Y_LEFT;
        stepperY.setSpeed(-STEPPER_SPEED);
      } 
      else if (cmd == "XU") { // ATAS
        if (currentState != MOVE_X_UP) Serial.println(F("ACK: XU"));
        currentState = MOVE_X_UP;
        stepperX.setSpeed(STEPPER_SPEED);
      } 
      else if (cmd == "XD") { // BAWAH
        if (currentState != MOVE_X_DOWN) Serial.println(F("ACK: XD"));
        currentState = MOVE_X_DOWN;
        stepperX.setSpeed(-STEPPER_SPEED);
      } 
      else if (cmd == "S" || cmd == "STOP") { // STOP / RELEASE
        if (currentState != IDLE) Serial.println(F("ACK: STOP"));
        stopAllMotors();
      }
    }
  }

  // 2. Safety Watchdog Timeout (Auto-Stop jika Web melepaskan tombol / putus jaringan)
  if (currentState != IDLE && (millis() - lastCommandTime > SAFETY_TIMEOUT_MS)) {
    stopAllMotors();
  }

  // 3. Eksekusi Gerakan Non-Blocking Realtime (Tanpa Delay)
  switch (currentState) {
    case MOVE_Y_RIGHT:
    case MOVE_Y_LEFT:
      stepperY.runSpeed();
      break;

    case MOVE_X_UP:
    case MOVE_X_DOWN:
      stepperX.runSpeed();
      break;

    case IDLE:
    default:
      break;
  }
}

void stopAllMotors() {
  currentState = IDLE;
  stepperX.setSpeed(0);
  stepperY.setSpeed(0);
  stepperX.stop();
  stepperY.stop();
  digitalWrite(ENABLE_PIN, LOW); // Tetap aktif agar posisi terkunci
}
