import asyncio
from cgi import print_directory
from rest_framework import generics, viewsets, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework import permissions
from django.contrib.auth.models import User
from .models import Device, Grid
from .serializers import *
from .mqtt_server import MqttServer
import json
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from decouple import config
from .utils import action_validation_wrapper

class DeviceListApiView(generics.ListCreateAPIView):
    # add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]
    # 1. List all
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer


class DeviceApiView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer
    lookup_field = 'id'
    queryset = Device.objects.all()

class DeviceNetApiView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NetworkSwitchSerializer

    def post(self, request: Request, *args, **kwargs):
        """
        Switch wireless network
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data()
        devices = Device.objects.filter(username=request.user,
                                        wifi_ssid=validated_data['old_wifi_ssid'])
        if devices.count > 0:
            for device in devices:
                MqttServer.getInstance().set_network(
                    device.wifi_ssid, device.local_address,
                    validated_data['wifi_ssid'], validated_data['wifi_pass'])
                # we need to send it once, and for every device value will be changed
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_NOT_FOUND)


class DeviceActionView(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceActionSerializer

    @action(["get"], detail=False)
    @action_validation_wrapper
    def dev_read(endpoint, clientID):
        MqttServer.getInstance().dev_read(endpoint, clientID)

    @action(["post"], detail=False)
    @action_validation_wrapper
    def dev_put(self, endpoint, clientID, payload):
        MqttServer.getInstance().dev_put(endpoint, clientID, payload)

    @action(["put"], detail=False)
    @action_validation_wrapper
    def dev_update(self, endpoint, clientID, payload):
        MqttServer.getInstance().dev_update(endpoint, clientID, payload)


class GridListView(generics.ListCreateAPIView):
    serializer_class = GridSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_query = User.objects\
            .filter(pk=self.request.user.pk)
        # length <= 1
        for user in user_query:
            devmas_query = user.device_masters.all()
            for dev in devmas_query:
                return dev.grids.all()


class StreamControllerView(generics.GenericAPIView):
    """
    Returns url to broker network
    """
    def get(self, request: Request, *args, **kwargs):
        return Response(
            data=config("URL_BROKER_NETWORK"),
            status=status.HTTP_200_OK)


class StreamViewConsumer(AsyncWebsocketConsumer):
    permission_classes = [permissions.IsAuthenticated]

    async def connect(self):
        self.groupname = "Stream"
        clientID = self.scope['url_route']['kwargs']['clientID']
        for head in self.scope['headers']:
            if head[0] == b'endpoint':
                endpoint = str(head[1])
        self.stream_name = clientID + endpoint
        self.stream_group_name = f'stream_{self.stream_name}'
        self.mqtt = MqttServer.getInstance()
        await self.accept()
        self.mqtt.connectStream(endpoint, clientID, self.stream_name)
        while (self.mqtt.callbackAvailable(endpoint, clientID)):
            if not self.mqtt.isEmptyStream(self.stream_name):
                data = self.mqtt.pullStream(self.stream_name)
                async_to_sync(self.send)(bytes_data=bytes(data))
                await asyncio.sleep(0.001)
                print(self.mqtt.streamMsgCount(self.stream_name))
                # print(data)

    async def disconnect(self, close_code):
        # Leave room group
        self.mqtt.disconnectStream(self.stream_name)
        await self.channel_layer.group_discard(
            self.stream_group_name,
        )
        await self.close()
