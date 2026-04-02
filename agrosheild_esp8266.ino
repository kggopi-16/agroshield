/*
 * AgroShield ESP8266 FINAL VERSION (HTTPS + STABLE)
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <DHT.h>

// ---------------- WIFI ----------------
const char* ssid = "moto g84";
const char* password = "12345678";

// ---------------- SERVER ----------------
// 🔥 Using HTTPS (FIXED 307 issue)
const char* serverUrl = "https://agroshield-edhg.onrender.com/api/sensor";

// ---------------- PINS ----------------
#define DHTPIN D2
#define DHTTYPE DHT11
#define SOIL_PIN A0

DHT dht(DHTPIN, DHTTYPE);

// ---------------- TIMING ----------------
unsigned long lastSend = 0;
const long interval = 10000;  // 10 seconds

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);
  dht.begin();

  Serial.println("\n🚀 AgroShield Starting...");

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// ---------------- LOOP ----------------
void loop() {

  if (millis() - lastSend >= interval) {
    lastSend = millis();

    if (WiFi.status() == WL_CONNECTED) {

      // -------- SENSOR --------
      float h = dht.readHumidity();
      float t = dht.readTemperature();
      int soilRaw = analogRead(SOIL_PIN);

      float m = map(soilRaw, 1024, 200, 0, 100);
      if (m < 0) m = 0;
      if (m > 100) m = 100;

      if (isnan(h) || isnan(t)) {
        Serial.println("❌ DHT read failed!");
        return;
      }

      // -------- JSON --------
      String jsonData = "{";
      jsonData += "\"humidity\":" + String(h) + ",";
      jsonData += "\"temperature\":" + String(t) + ",";
      jsonData += "\"moisture\":" + String(m) + ",";
      jsonData += "\"ph\":6.5";
      jsonData += "}";

      Serial.println("\n📡 Sending:");
      Serial.println(jsonData);

      // -------- HTTPS REQUEST --------
      WiFiClientSecure client;
      client.setInsecure();   // 🔥 IMPORTANT (skip SSL verify)

      HTTPClient http;
      http.setTimeout(5000);

      if (http.begin(client, serverUrl)) {

        http.addHeader("Content-Type", "application/json");

        int httpResponseCode = http.POST(jsonData);

        if (httpResponseCode > 0) {
          Serial.print("✅ Response: ");
          Serial.println(httpResponseCode);

          String response = http.getString();
          Serial.println("Server: " + response);

        } else {
          Serial.print("❌ Error: ");
          Serial.println(httpResponseCode);
        }

        http.end();

      } else {
        Serial.println("❌ HTTP begin failed!");
      }

    } else {
      Serial.println("⚠️ WiFi lost! Reconnecting...");
      WiFi.begin(ssid, password);
    }
  }

  yield(); // keep WiFi stable
}