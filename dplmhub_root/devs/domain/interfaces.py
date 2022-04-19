from devs.serializers import DeviceSerializer, DeviceReadLogSerializer, GridSerializer
from devs.models import Device, DeviceReadLog, Endpoint, Grid
from rest_framework import serializers
from .mqtt_client import MqttClient
from abc import ABC, abstractmethod
from userAuth.models import DeviceMaster
from django.contrib.auth.models import User
from rest_framework import exceptions as api_exc


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
        # remember dev [clientID, user, local_address, broker_address, wifi_ssid]
        attributes = msg.payload.decode('utf-8').split(':')
        user = User.objects.filter(username=attributes[1]).first()
        if user is None:
            return
        device_master = user.device_masters.all().first()
        data = {
            'clientID': attributes[0],
            'user': device_master.id,
            'local_address': attributes[2]
        }
        wifi_ssid = attributes[4]
        grids = device_master.grids.filter(wifi_ssid=wifi_ssid)
        grid = None
        if grids.count() > 0:
            grid = grids.first()
        else:
            grid_ser = GridSerializer(data={
                'user': device_master.id,
                'broker_address': attributes[3],
                'wifi_ssid': wifi_ssid
            })
            try:
                grid_ser.is_valid(raise_exception=True)
                grid = grid_ser.save()
            except serializers.ValidationError as e:
                print(f'Failed creating grid {e.detail}')
        if grid is None:
            print('Registration: not found grid')
            return
        serializer = DeviceSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            device = serializer.save()
        except serializers.ValidationError as e:
            device = device_master.devices.filter(
                clientID=serializer.data['clientID']).first()
        if device is None:
            print('Registration: not found device')
            return
        device.grid = grid
        device.save(force_update=True)



    @staticmethod
    def callback_read(client, userdata, msg, clientID: str, endpoint: str):
        byte_data = msg.payload
        device = Device.objects.filter(clientID=clientID).first()
        endpoint_instance = Endpoint.objects.filter(
            name=endpoint, device=device.id
        ).first()
        if device is None or endpoint_instance is None:
            print('Mqtt callback not found device or instance, can\'t save read')
            return
        serializer = DeviceReadLogSerializer(data={
            "device": device.id,
            "data": byte_data,
            "endpoint": endpoint_instance.id,
        })
        if serializer.is_valid():
            DeviceReadLog.objects.create(
                device=device,
                data=byte_data,
                endpoint=endpoint_instance
            )

    @staticmethod
    def callback_status_network(
            client, userdata, msg,
            clientID, new_ssid, old_ssid
            ):
        device = Device.objects.filter(clientID=clientID).first()
        device_master = DeviceMaster.objects.filter(id=device.user.id).first()
        old_grid = device_master.grids.filter(old_ssid).first()
        new_grid = device_master.grids.filter(new_ssid).first()
        if device is not None:
            if msg.payload == '1':
                if new_grid is None:
                    grid_ser = GridSerializer(data={
                        'user': device_master.id,
                        'broker_address': old_grid.broker_address,
                        'wifi_ssid': device.wifi_ssid
                    })
                    if grid_ser.is_valid():
                        new_grid = grid_ser.save()
                device.grid = new_grid
                if old_grid is not new_grid:
                    if old_grid.devices.all().count() == 0:
                        old_grid.delete()
            elif msg.payload == '0':
                device.grid = old_grid
            device.save(force_update=True)

    @staticmethod
    def callback_deviceAAD(client, userdata, msg):
        pass

def get_mqttgate_factory() -> GatewayFactory:
    gate = MqttGatewayFactory()
    return gate
