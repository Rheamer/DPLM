from .serializers import DeviceSerializer
from mqtt_client import MqttClient
from abc import ABC, abstractmethod
import threading

def callback_registration(client, userdata, msg):
    print("MQTT endpoint received: " + msg.topic)
    # remember dev [clientID, user, local_address, last_update_date]
    attributes = msg.payload.decode('utf-8').split(':')
    data = {
        'clientID': attributes[0],
        'user': attributes[1],
        'local_address': attributes[2],
    }
    serializer = DeviceSerializer(data=data)
    if serializer.is_valid():
        serializer.save()

def callback_read(client, userdata, msg):
    pass
    # read msg []

MqttClient.callback_registration = callback_registration
# TODO: define callbacks
MqttClient.callback_read = None
MqttClient.callback_status_network = None
MqttClient.callback_deviceAAD = None

# TODO: create gateway client interface, then pass it to device gateway facade
class GatewayClient(ABC):
    pass

class DeviceGateway:
    _device_gateway_client = MqttClient

    def get_instance(self):
        return self._device_gateway_client.get_instance()


threading.Thread(target=MqttClient.run_mqtt_server).start()