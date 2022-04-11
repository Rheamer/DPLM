from devs.serializers import DeviceSerializer, DeviceReadLogSerializer
from devs.models import Device
from .mqtt_client import MqttClient
from abc import ABC, abstractmethod
from userAuth.models import DeviceMaster
from django.contrib.auth.models import User

# interface for gateway client instance, to switch out mqtt and coap for example
# TODO: create gateway client interface, gateway's factory get_instance should
#  declare return type as interface
class GatewayClient(ABC):
    pass


class GatewayFactory(ABC):
    _gateway_client = None

    @abstractmethod
    def _setup(self) -> None:
        pass

# TODO: change return type to interface
    @classmethod
    def get_instance(cls):
        instance = cls._gateway_client.get_instance()
        return instance


class MqttGatewayFactory(GatewayFactory):
    _gateway_client = MqttClient

    def __init__(self):
        self._setup()

    def _setup(self) -> None:
        self._gateway_client.callbacks['registration'] = self.callback_registration
        self._gateway_client.callbacks['read'] = self.callback_read
        self._gateway_client.callbacks['status_network'] = self.callback_status_network
        self._gateway_client.callbacks['deviceAAD'] = self.callback_deviceAAD

    @staticmethod
    def callback_registration(client, user_data, msg):
        print("MQTT endpoint received: " + msg.topic)
        # remember dev [clientID, user, local_address, last_update_date]
        attributes = msg.payload.decode('utf-8').split(':')
        device_master = User.objects.filter(username=attributes[1]).first()\
            .device_masters.all().first()
        data = {
            'clientID': attributes[0],
            'user': device_master.id,
            'local_address': attributes[2],
        }
        serializer = DeviceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

    @staticmethod
    def callback_read(client, userdata, msg, deviceID, endpoint):
        serializer = DeviceReadLogSerializer(data = {
            "device": deviceID,
            "data": msg.payload,
            "endpoint": endpoint,
        })
        # TODO serialize read log not action
        if serializer.is_valid():
            serializer.save()

    # TODO: define callbacks
    @staticmethod
    def callback_status_network(
            client, userdata, msg,
            clientID, new_ssid, old_ssid
            ):
        device = Device.objects.filter(clientID=clientID).first()
        if device is not None:
            if msg.payload == '1':
                device.wifi_ssid = new_ssid
            elif msg.payload == '0':
                device.wifi_ssid = old_ssid
            device.save()

    @staticmethod
    def callback_deviceAAD(client, userdata, msg):
        pass

def get_mqttgate_factory() -> GatewayFactory:
    gate = MqttGatewayFactory()
    return gate
