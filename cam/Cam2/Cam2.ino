#include "esp_camera.h"
#include "Arduino.h"
#include "soc/soc.h"           // Disable brownour problems
#include "soc/rtc_cntl_reg.h"  // Disable brownour problems
#include "driver/rtc_io.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h> //ArduinoJSON6
DynamicJsonDocument CONFIG(2048);

const char* ssid = "";
const char* password = "";
const char* mqtt_server = "";
const char* HostName = "cam2_Gas";
const char* topic_PHOTO = "/cam2/photo";
const char* topic_CONFIG = "/cam2/setup";
const char* topic_SLEEP = "/cam2/sleep";
const char* topic_UP = "/cam2/cam";
const char* mqttUser = "";
const char* mqttPassword = "";
WiFiClient espClient;
PubSubClient client(espClient);

void callback(String topic, byte* message, unsigned int length) {
  String messageTemp;
  for (int i = 0; i < length; i++) {
    messageTemp += (char)message[i];
  }
  if (topic == topic_PHOTO) {
    Serial.println("PING");
    take_picture(messageTemp);
  }
  if (topic == topic_SLEEP) {
    if(messageTemp == "Sleep_now"){
     ESP.deepSleep(30*60000000); //Angabe in Minuten - hier 30
     Serial.println("Going to sleep");
      //ESP.deepSleep(10000000); // Schlafe 10sek
        }
   }
  if (topic == topic_CONFIG) {
    deserializeJson(CONFIG, messageTemp);
    Serial.println(messageTemp);
    sensor_t * s = esp_camera_sensor_get();
    s->set_framesize(s, FRAMESIZE_VGA); //QVGA|CIF|VGA|SVGA|XGA|SXGA|UXGA
    s->set_vflip(s, CONFIG["vflip"]); //0 - 1
    s->set_hmirror(s, CONFIG["hmirror"]); //0 - 1
    s->set_colorbar(s, CONFIG["colorbar"]); //0 - 1
    s->set_special_effect(s, CONFIG["special_effect"]); // 0 - 6
    s->set_quality(s, CONFIG["quality"]); // 0 - 63
    s->set_brightness(s, CONFIG["brightness"]); // -2 - 2
    s->set_contrast(s, CONFIG["contrast"]); // -2 - 2
    s->set_saturation(s, CONFIG["saturation"]); // -2 - 2
    s->set_sharpness(s, CONFIG["sharpness"]); // -2 - 2
    s->set_denoise(s, CONFIG["denoise"]); // 0 - 1
    s->set_awb_gain(s, CONFIG["awb_gain"]); // 0 - 1
    s->set_wb_mode(s, CONFIG["wb_mode"]); // 0 - 4
    
  }
}

void camera_init() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = 5;
  config.pin_d1       = 18;
  config.pin_d2       = 19;
  config.pin_d3       = 21;
  config.pin_d4       = 36;
  config.pin_d5       = 39;
  config.pin_d6       = 34;
  config.pin_d7       = 35;
  config.pin_xclk     = 0;
  config.pin_pclk     = 22;
  config.pin_vsync    = 25;
  config.pin_href     = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn     = 32;
  config.pin_reset    = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size   = FRAMESIZE_XGA; // QVGA|CIF|VGA|SVGA|XGA|SXGA|UXGA
  config.jpeg_quality = 10;           
  config.fb_count     = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
}

void take_picture(String msg) {
  camera_fb_t * fb = NULL;
  if (msg == "Flash"){
    digitalWrite(4, HIGH);
    delay(1000);
  }
  fb = esp_camera_fb_get();
  digitalWrite(4, LOW);
  String daten = "";
  unsigned int count = fb->len; 
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  if (MQTT_MAX_PACKET_SIZE == 128) {
    //SLOW MODE (increase MQTT_MAX_PACKET_SIZE)
    if(!client.publish_P(topic_UP, fb->buf, count, false)){
      Serial.println("Published failed");
    }
  }
  else {
    //FAST MODE (increase MQTT_MAX_PACKET_SIZE)
     if(!client.publish_P(topic_UP, fb->buf, count, false)){
      Serial.println("Published failed");
    }
  }
  Serial.println("CLIC");
  esp_camera_fb_return(fb);
  
  // Turns off the ESP32-CAM white on-board LED (flash) connected to GPIO 4

}
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(HostName);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(HostName,mqttUser,mqttPassword)) {
      Serial.println("connected");
      client.subscribe(topic_PHOTO);
      client.subscribe(topic_CONFIG);
      client.subscribe(topic_SLEEP);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void send_awake(){
  String sleep_req = "Sleep?";
  client.publish(topic_SLEEP, sleep_req.c_str());
  Serial.println("Sleep request");
}

void setup() {
  pinMode(4, OUTPUT);
  Serial.begin(115200);
  camera_init();
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  reconnect();
  send_awake();
}
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
