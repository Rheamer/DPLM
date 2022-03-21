from .serializers import DeviceSerializer, DeviceActionSerializer
from .models import Device
from .mqtt_client import MqttClient
from abc import ABC, abstractmethod


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


def callback_read(client, userdata, msg, deviceID, endpoint):
    serializer = DeviceActionSerializer(data={
        'value': msg.payload,
        'endpoint': endpoint}
    )
    if serializer.is_valid():
        obj = serializer.instance
        query = Device.objects.filter(clientID=deviceID)
        obj.device = query.get(0).id
        obj.save()


# TODO: define callbacks
def callback_status_network(client, userdata, msg):
    pass


def callback_deviceAAD(client, userdata, msg):
    pass

# interface for gateway client instance, to switch out mqtt and coap for example
# TODO: create gateway client interface, gateway's factory get_instance should
#  declare return type as interface
class GatewayClient(ABC):
    pass


class GatewayFactory(ABC):
    _gateway_client = None

    @abstractmethod
    def setup(self) -> None:
        pass

# TODO: change return type to interface
    @classmethod
    def get_instance(cls):
        instance = cls._gateway_client.get_instance()
        return instance


class MqttGatewayFactory(GatewayFactory):
    _gateway_client = MqttClient

    def setup(self) -> None:
        self._gateway_client.callback_registration = callback_registration
        self._gateway_client.callback_read = callback_read
        self._gateway_client.callback_status_network = callback_status_network
        self._gateway_client.callback_deviceAAD = callback_deviceAAD


def get_gateway_factory() -> GatewayFactory:
    return MqttGatewayFactory()
