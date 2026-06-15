#include <Arduino.h>
#include <BluetoothSerial.h>
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN  22
#define SS_PIN   5
#define LED_PIN 13

MFRC522 rfid(SS_PIN, RST_PIN);
BluetoothSerial SerialBT;

String cmdBuffer = "";
bool deauthActive = false;
unsigned long deauthStartTime = 0;
const unsigned long DEAUTH_DURATION = 30000;
const int DEAUTH_INTERVAL = 100;
String deauthTargetMAC = "";

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
  digitalWrite(LED_PIN, HIGH);

  Serial.println();
  Serial.println("Booting...");
  Serial.flush();

  SPI.begin();
  SerialBT.begin("ESP32_NFC_MultiTester");

  delay(500);
  rfid.PCD_Init();
  delay(200);

  byte v = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  Serial.print("RC522 version: 0x");
  Serial.println(v, HEX);
  Serial.flush();

  if (v != 0 && v != 0xFF) {
    SerialBT.println("Prosivka Verify");
    Serial.println("Prosivka Verify");
  } else {
    SerialBT.println("ERROR:2");
    Serial.println("ERROR:2");
  }

  digitalWrite(LED_PIN, LOW);
}

void loop() {
  if (deauthActive) {
    if (millis() - deauthStartTime < DEAUTH_DURATION) {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      SerialBT.print("[BT_DEAUTH] Sending deauth to ");
      SerialBT.print(deauthTargetMAC);
      SerialBT.print(" | packet ");
      SerialBT.println((millis() - deauthStartTime) / DEAUTH_INTERVAL);
      delay(DEAUTH_INTERVAL);
    } else {
      deauthActive = false;
      digitalWrite(LED_PIN, LOW);
      SerialBT.println("[BT_DEAUTH] Attack simulation finished (30s).");
    }
    return;
  }

  if (SerialBT.available()) {
    char c = SerialBT.read();
    if (c == '\n') {
      processCommand(cmdBuffer);
      cmdBuffer = "";
    } else if (c != '\r') {
      cmdBuffer += c;
    }
  }

  if (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      processSerialCommand(cmdBuffer);
      cmdBuffer = "";
    } else if (c != '\r') {
      cmdBuffer += c;
    }
  }

  delay(10);
}

void processCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd == "PING") {
    SerialBT.println("PONG");
  } else if (cmd == "READ_NFC") {
    handleReadNFC();
  } else if (cmd.startsWith("WRITE_NFC:")) {
    handleWriteNFC(cmd.substring(10));
  } else if (cmd.startsWith("BT_DEAUTH:")) {
    handleBTDeauth(cmd.substring(10));
  } else {
    SerialBT.println("ERROR: Unknown command");
  }
}

void processSerialCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd == "PING") Serial.println("PONG");
  else if (cmd == "READ_NFC") handleReadNFC();
  else if (cmd.startsWith("WRITE_NFC:")) handleWriteNFC(cmd.substring(10));
  else if (cmd.startsWith("BT_DEAUTH:")) handleBTDeauth(cmd.substring(10));
}

void handleReadNFC() {
  SerialBT.println("Place NFC tag near the reader...");
  unsigned long startTime = millis();
  const unsigned long TIMEOUT = 10000;

  while (millis() - startTime < TIMEOUT) {
    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
      String uidStr = "";
      for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
        uidStr += String(rfid.uid.uidByte[i], HEX);
        if (i < rfid.uid.size - 1) uidStr += " ";
      }
      uidStr.toUpperCase();

      String dataStr = "";
      byte buffer[18];
      byte block = 1;
      byte size = sizeof(buffer);

      MFRC522::StatusCode status = (MFRC522::StatusCode)rfid.MIFARE_Read(block, buffer, &size);
      if (status == MFRC522::STATUS_OK) {
        for (byte i = 0; i < 16; i++) {
          if (buffer[i] >= 0x20 && buffer[i] <= 0x7E) dataStr += (char)buffer[i];
          else dataStr += ".";
        }
      } else {
        dataStr = "N/A";
      }

      SerialBT.print("UID: ");
      SerialBT.print(uidStr);
      SerialBT.print(" Data: ");
      SerialBT.println(dataStr);

      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
      return;
    }
    delay(100);
  }

  SerialBT.println("NO_CARD");
}

void handleWriteNFC(String data) {
  if (data.length() > 100 || data.length() == 0) {
    SerialBT.println("WRITE_ERROR");
    return;
  }

  SerialBT.println("Place NFC tag to write...");
  unsigned long startTime = millis();
  const unsigned long TIMEOUT = 10000;

  while (millis() - startTime < TIMEOUT) {
    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
      MFRC522::MIFARE_Key key;
      for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;

      MFRC522::StatusCode status = (MFRC522::StatusCode)rfid.PCD_Authenticate(
        MFRC522::PICC_CMD_MF_AUTH_KEY_A, 1, &key, &(rfid.uid));

      if (status != MFRC522::STATUS_OK) {
        SerialBT.println("WRITE_ERROR: Auth");
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();
        return;
      }

      byte buffer[16];
      for (int i = 0; i < 16; i++) {
        buffer[i] = (i < data.length()) ? data[i] : 0;
      }

      status = (MFRC522::StatusCode)rfid.MIFARE_Write(1, buffer, 16);
      if (status == MFRC522::STATUS_OK) {
        SerialBT.println("WRITE_OK");
      } else {
        SerialBT.println("WRITE_ERROR");
      }

      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
      return;
    }
    delay(100);
  }

  SerialBT.println("WRITE_ERROR: No card");
}

void handleBTDeauth(String mac) {
  mac.trim();
  if (mac.length() == 0) {
    SerialBT.println("BT_DEAUTH_ERROR: No MAC");
    return;
  }

  SerialBT.println("WARNING: Use only on your own devices! Illegal without permission.");
  delay(2000);

  deauthTargetMAC = mac;
  deauthActive = true;
  deauthStartTime = millis();

  SerialBT.print("[BT_DEAUTH] Starting deauth simulation against ");
  SerialBT.print(mac);
  SerialBT.println(" for 30s");
}
