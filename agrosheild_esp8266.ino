/*
 * AgroShield ESP8266 - LOCAL IP VERSION
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h> 
#include <DHT.h>

// ---------------- WIFI ----------------
const char* ssid = "moto";
const char* password = "124567890";

// ---------------- SERVER ----------------
// 🔥 Production URL (Render)
const char* serverUrl = "https://agroshield-edhg.onrender.com/api/sensor"; 

// ---------------- PINS ----------------
#define DHTPIN D2
#define DHTTYPE DHT11
#define SOIL_PIN A0

DHT dht(DHTPIN, DHTTYPE);

unsigned long lastSend = 0;
const long interval = 10000; 

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connected!");
  Serial.print("ESP8266 IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(ssid, password);
    delay(2000);
    return;
  }

  if (millis() - lastSend >= interval) {
    lastSend = millis();

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    int soilRaw = analogRead(SOIL_PIN);
    float m = constrain(map(soilRaw, 1024, 200, 0, 100), 0, 100);

    if (isnan(h) || isnan(t)) return;

    // JSON Construction
    String jsonData = "{\"humidity\":" + String(h) + 
                      ",\"temperature\":" + String(t) + 
                      ",\"moisture\":" + String(m) + 
                      ",\"ph\":6.5}";

    WiFiClientSecure client;
    client.setInsecure(); // 🔥 Required for HTTPS (Render)
    HTTPClient http;
    http.setTimeout(5000); 

    Serial.println("\nAttempting to send to: " + String(serverUrl));

    if (http.begin(client, serverUrl)) {
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(jsonData);

      if (httpResponseCode > 0) {
        Serial.printf("✅ Success! Code: %d\n", httpResponseCode);
        Serial.println("Response: " + http.getString());
      } else {
        // 🔥 If you see "-1", it's usually a Firewall or wrong IP
        Serial.printf("❌ Error: %s (%d)\n", http.errorToString(httpResponseCode).c_str(), httpResponseCode);
      }
      http.end();
    }
  }
  yield();
}
