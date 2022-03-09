import asyncio
from cgi import print_directory
from rest_framework import generics
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

class DeviceListApiView(generics.ListCreateAPIView):
    # add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]
    # 1. List all
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    # def get(self, request, *args, **kwargs):
    #     '''
    #     List all the tod items for given requested user
    #     '''
    #     devices = Device.objects.filter()
    #     serializer = DeviceSerializer(devices, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    #
    # # 2. Create
    # def post(self, request, *args, **kwargs):
    #     '''
    #     Create the Device with given device data
    #     '''
    #     data = {
    #         'clientID': request.data.get('clientID'),
    #         'user': request.data.get('user'),
    #         'local_address': request.data.get('local_address'),
    #         # 'user': request.user.id
    #     }
    #     serializer = DeviceSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class DeviceActionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer
    # TODO: make serializers to format control requests
    # TODO: maybe it's better to use GenericViewSet with
    def get(self, request: Request, *args, **kwargs):
        dev_endpoint = request.headers['endpoint']
        clientID = request.headers['clientID']
        print('Read ' + clientID)
        devices = Device.objects.filter(clientID=clientID)
        # should only one device found
        if devices.count() > 1:
            print('Found repeating clientID query!')
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if devices.count() == 0:
            return Response(data="No device with provided ID",
                            status=status.HTTP_404_NOT_FOUND)
        MqttServer.getInstance().dev_read(dev_endpoint, clientID)
        return Response(status=status.HTTP_200_OK)

    def post(self, request: Request, *args, **kwargs):
        dev_endpoint = request.headers['endpoint']
        clientID = request.headers['clientID']
        payload = request.headers['payload']
        print('Put ' + clientID)
        devices = Device.objects.filter(clientID=clientID)
        # should only be one device found
        if devices.count() > 1:
            print('Found repeating clientID query!')
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if devices.count() == 0:
            return Response(data="No device with provided ID",
                            status=status.HTTP_404_NOT_FOUND)
        MqttServer.getInstance().dev_put(dev_endpoint, clientID, payload)
        return Response(status=status.HTTP_200_OK)

    def update(self, request: Request, *args, **kwargs):
        dev_endpoint = request.headers['endpoint']
        clientID = request.headers['clientID']
        payload = request.headers['payload']
        print('Update ' + clientID)
        devices = Device.objects.filter(clientID=clientID)
        # should only be one device found
        if devices.count() > 1:
            print('Found repeating clientID query!')
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if devices.count() == 0:
            return Response(data="No device with provided ID",
                            status=status.HTTP_404_NOT_FOUND)
        MqttServer.getInstance().dev_update(dev_endpoint, clientID, payload)
        return Response(status=status.HTTP_200_OK)


class GridListView(generics.ListCreateAPIView):
    serializer_class = GridSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Grid.objects.all()\
            .select_related('user') \
            .select_related('user') \
            .filter(username=self.request.user)

    # def get(self, request: Request, *args, **kwargs):
    #     '''
    #     Get list of grids including devices
    #     '''
    #
        # query = Device.objects.all().select_related('grid') \
        #     .select_related('user') \
        #     .select_related('user') \
        #     .filter(username=request.user)
    #     if query.count() <= 0:
    #         return Response(status=status.HTTP_404_NOT_FOUND)
    #     serializer = GridSerializer(query, many=True)
    #
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    #
    # def post(self, request: Request, *args, **kwargs):
    #     '''
    #     Create the Grid
    #     '''
    #     data = {
    #         'user': request.data.get('user'),
    #         'broker_name': request.data.get('broker_name'),
    #         'broker_address': request.data.get('broker_address'),
    #         'wifi_ssid': request.data.get('wifi_ssid'),
    #     }
    #     serializer = GridSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# TODO: get grid devices view with grid ID

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
        # await self.accept()ID
        # # def sendLoop():
        # self.mqtt = MqttServer.getInstance()
        # self.mqtt.connectStream(endpoint, self.stream_name)
        # while (self.mqtt.streamAvailable(endpoint, self.stream_name)):
        #     if not self.mqtt.isEmptyStream(endpoint, self.stream_name):
        #         data = self.mqtt.pullStream(endpoint, self.stream_name)
        #         sync_to_async(self.send)(bytes_data = bytes(data))
        #         print(self.mqtt.streamMsgCount(endpoint, self.stream_name))
        # sync_to_async(sendLoop)()

        # self.groupname = "Stream"
        # self.stream_name = self.scope['url_route']['kwargs']['clientID']
        # self.stream_group_name = f'stream_{self.stream_name}'
        self.mqtt = MqttServer.getInstance()
        # await self.channel_layer.group_add(
        # self.stream_group_name,
        # self.channel_name
        # )
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
