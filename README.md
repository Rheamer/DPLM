# DPLM
IoT Project

__MICROCONTROLLERS__  
__PubSubClient client for MQTT messaging__
Connect to local/mother mosquitto broker node. Subscribe to all functional endpoints that correspond to a real actuator/sensor.    

__SERVER__  
__Django, DRF, postgresql, paho-mqtt, Asyncio__   
User management, access to mosquitto, microcontroller related actions (read, write, network configuration).  
_Broker_ is used for sensor data streaming, server implements REST API endpoints for confirmation.  
  
__DESKTOP__  
__QT, cpp-http, python embedding, matplotlib__    
User UI, authentication, sessions, listings, real-time plotting.  