#include <WiFi.h>
#include <PubSubClient.h>
#include <Array.h>
#include <LCD_I2C.h>

const String base_ssid = "";
const String base_wifi_password = "";
String ssid = base_ssid;
String wifi_password = base_wifi_password;
String clientID = "";
String user = "";
String password = "";

LCD_I2C lcd(0x27, 16, 2);

const int ONBOARD_LED = 2;
const int ADC34 = 34;

const String base_mqtt_server = "";
String  mqtt_server = base_mqtt_server;
const int base_mqtt_port = 0;
int mqtt_port = base_mqtt_port;

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi(String const& _ssid, String const& _pass) {
  delay(10);
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(_ssid);

    WiFi.begin(_ssid.c_str(), _pass.c_str());
  }

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

int setup_wifi_timed(String const& _ssid, String const& _pass) {
  delay(10);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(_ssid);

  WiFi.begin(_ssid.c_str(), _pass.c_str());
  int timer = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (++timer > 20) {
      return -1;
    }
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  return 0;
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.println(topic);
  String strtopic = String(topic);
  if (strtopic == "action/put/serial/" + clientID) {
    callback_serial(message, length);
  } else if (strtopic == "discovery/local") {
    callback_discovery_local(message, length);
  } else if (strtopic == "config/net/" + WiFi.localIP().toString() + ":" + ssid) {
    callback_setNetwork(message, length);
  } else if (strtopic == "action/update/blink/" + clientID) {
    callback_blink(message, length);
  } else if (strtopic == "action/update/lcd/" + clientID) {
    callback_lcd(message, length);
  } else if (strtopic == "config/broker/" + clientID) {
    callback_broker(message, length);
  } else if (strtopic == "action/getread/phres/" + clientID) {
    callback_read_phres(message, length);
  }
}

void callback_read_phres(byte* message, unsigned int length) {
   String sread = String(analogRead(ADC34));
   client.publish(("action/read/phres" + String("/") + clientID ).c_str(),
                   sread.c_str(), sread.length());
}

void callback_serial(byte* message, unsigned int length) {
   String txt;
   txt.reserve(length);
   for (int i = 0; i < length; ++i)
    txt[i] = message[i];
   Serial.println(txt);
}

void callback_discovery_local(byte* message, unsigned int length) {
   String txt;
   txt.reserve(length);
   for (int i = 0; i < length; ++i)
    txt[i] = message[i];
   Serial.println(txt);
}

void callback_setNetwork(byte* msg, unsigned int length) {
  // newSsid:newPassword
  String newSsid, newPass;
  for (int i = 0; i < length; i++) {
    if (msg[i] == ':') {
      for (int j = 0; j < i; j++)
        newSsid += msg[j];
      for (int j = i + 1; j < length; j++)
        newPass += msg[j];
    }
    if (!setup_wifi_timed(newSsid, newPass)) {
      String topic = "config/net/status/" + WiFi.localIP().toString() + ":" + ssid;
      String msg = "1";
      client.publish(topic.c_str(), msg.c_str());
      ssid = newSsid;
      wifi_password = newPass;
    } else { // no success
      setup_wifi(ssid, wifi_password);
      String topic = "config/net/status/" + WiFi.localIP().toString() + ":" + ssid;
      String msg = "0";
      client.publish(topic.c_str(), msg.c_str());
    }
  }
}

void callback_blink(byte* msg, unsigned int length) {
  if (length > 1 || length == 0)
    return;
  Serial.print(msg[0]);
  Serial.print(length);
  int blink_count = int(msg[0]);
  for (int i = 0; i < blink_count; ++i) {
    delay(500);
    digitalWrite(ONBOARD_LED, HIGH);
    delay(500);
    digitalWrite(ONBOARD_LED, LOW);
  }
}

void callback_lcd(byte* msg, unsigned int length) {
  String line;
  if (length > 50){
    return;
  }
  for (int i = 0; i < length; i++){
    line += (char)msg[i];
  }
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(line);
}

void reconnect() {
  // Loop until we're reconnected
  int until_reset = 5;
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(clientID.c_str(), user.c_str(), password.c_str())) {
      Serial.println("connected");
      
      client.subscribe(("config/net/" + WiFi.localIP().toString() + ":" + ssid).c_str());
      client.subscribe(("config/broker/" + clientID).c_str());
      client.subscribe(("action/update/blink/" + clientID).c_str());
      client.subscribe(("action/update/lcd/" + clientID).c_str());
      client.subscribe(("action/put/serial/" + clientID).c_str());
      client.subscribe(("action/getread/phres/" + clientID).c_str());
      client.subscribe("discovery/local");
      client.publish("discovery/registration",
                     (clientID + 
                     ":" + user + 
                     ":" + WiFi.localIP().toString() + 
                     ":" + mqtt_server +
                     ":" + ssid).c_str());
      client.publish("discovery/local", clientID.c_str());
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying

      delay(5000);
      if (--until_reset == 0){
        mqtt_server = base_mqtt_server;
        mqtt_port = base_mqtt_port;
        client.setServer(mqtt_server.c_str(), mqtt_port);
      }
    }
  }
}


void callback_broker(byte* msg, unsigned int length){
  // msg = ["broker_adress", "broker_port"]
  Serial.print("Switching broker");
  String broker_address, broker_port;
  for (int i = 0; i < length; ++i) {
    if (msg[i] == ':') {
      for (int j = 0; j < i; ++j)
        broker_address += msg[j];
      for (int j = i + 1; j < length; ++j)
        broker_port += msg[j];
    }
  }
  mqtt_server = broker_address;
  mqtt_port = broker_port.toInt();
  client.setServer(mqtt_server.c_str(), mqtt_port);
  reconnect();
}

int sensorRead = 0;
const int readBufferSize = 200;
Array<unsigned char, readBufferSize> sensorReadings;
int circularIndex = readBufferSize - 1; //will become 0 at start

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  sensorRead = analogRead(ADC34) + 1;
//  Serial.println(sensorRead);
  if (++circularIndex == readBufferSize) {
    circularIndex = 0;
    client.publish(("action/stream/phres" + String("/") + clientID ).c_str(),
                   sensorReadings.data(), readBufferSize);
  }
  sensorReadings[circularIndex] = (unsigned char)sensorRead;
  client.loop();

}

void setup() {
  Serial.begin(115200);
    lcd.begin(); 
    lcd.backlight();
  setup_wifi(ssid, wifi_password);
  client.setServer(mqtt_server.c_str(), mqtt_port);
  client.setCallback(callback);

  pinMode(ONBOARD_LED, OUTPUT);
  pinMode(ADC34, INPUT);
  const String conPoints =
    "blink(void)[u]\"impulse, blink few secs\""
  + String(":sensor(int)[r]\"highfreq,photores\"")
  + String(":serial(str)[u]\"serialout\"");
  reconnect();
  client.publish("discovery/aad",(clientID + ":" + conPoints).c_str());
}


  //void callback_discovery_local(byte* message, unsigned int length) {
  // Serial.print("[GET] Device discovered by ");
  // Serial.println(ip.toString() + ":" + String(port));
  // String m = "OK";
  // coap.sendResponse(ip, port, packet.messageid, m.c_str(), m.length(),
  //           COAP_RESPONSE_CODE::COAP_CONTENT, COAP_CONTENT_TYPE::COAP_TEXT_PLAIN,
  //           packet.token, packet.tokenlen);
  //}

  //void callback_status(byte* message, unsigned int length) {
  // Serial.print("[GET] Request status ");
  // Serial.println(ip.toString() + ":" + String(port));
  // String m = status.enabled ? "Board is active" : "Board is inactive";
  // m += "\n";
  // coap.sendResponse(ip, port, packet.messageid, m.c_str(), m.length(),
  //           COAP_RESPONSE_CODE::COAP_CONTENT, COAP_CONTENT_TYPE::COAP_TEXT_PLAIN,
  //           packet.token, packet.tokenlen);
  //}

//void callback_switch_status(byte* message, unsigned int length) {
  // Serial.print("[UPDATE] Request status ");
  // Serial.println(ip.toString() + ":" + String(port));
  // char p[packet.payloadlen + 1];
  // memcpy(p, packet.payload, packet.payloadlen);
  // p[packet.payloadlen] = NULL;
  // String client_p = p;
  // COAP_RESPONSE_CODE response_code = COAP_RESPONSE_CODE::COAP_CHANGED;
  // if (client_p == "1")
  //   status.enabled = true;
  // else if (client_p == "0")
  //   status.en5abled = false;
  // else
  //   response_code = COAP_RESPONSE_CODE::COAP_BAD_REQUEST;
  // coap.sendResponse(ip, port, packet.messageid, "", 0,
  //           response_code, COAP_CONTENT_TYPE::COAP_NONE,
  //           packet.token, packet.tokenlen);
//}