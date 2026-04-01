/*
 * AgroShield ESP8266 (NodeMCU) Firmware
 * Sensors: DHT11 (Temp/Humidity) + Analog Soil Moisture
 * 
 * Instructions:
 * 1. Install "DHT sensor library" by Adafruit via Library Manager.
 * 2. Change SSID and PASSWORD.
 * 3. Change SERVER_URL to your Render URL or local IP.
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>

// WiFi Credentials
const char* ssid = "moto g84";
const char* password = "12345678";

// Server Configuration
// For Local: "http://192.168sensor.1.XX:8000/api/"
// For Render: "http://your-app.onrender.com/api/sensor" 
// Note: Use http if not using SSL certificates on ESP, Render supports http redirect.
// const char* serverUrl = "http://your-app.onrender.com/api/sensor";
const char* serverUrl = "http://127.0.0.1:8000/api/sensor";

// Pin Configuration
#define DHTPIN D2           // DHT11 Data Pin
#define DHTTYPE DHT11       // DHT 11
#define SOIL_PIN A0         // Analog Soil Moisture Pin

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;

    // Read Sensors
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    int soilRaw = analogRead(SOIL_PIN);
    
    // Convert Soil Moisture to Percentage (0-100)
    // 1024 is dry, ~200 is wet (adjust based on your sensor)
    float m = map(soilRaw, 1024, 200, 0, 100);
    if (m < 0) m = 0;
    if (m > 100) m = 100;

    if (isnan(h) || isnan(t)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    // Prepare JSON Data
    String jsonData = "{\"humidity\": " + String(h) + 
                      ", \"temperature\": " + String(t) + 
                      ", \"moisture\": " + String(m) + 
                      ", \"ph\": 6.5}"; // pH is simulated or fixed for now

    Serial.println("Sending data: " + jsonData);

    // Start HTTP Connection
    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("HTTP Response code: " + String(httpResponseCode));
      Serial.println(response);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }

  // Send data every 10 seconds
  delay(10000);
}
