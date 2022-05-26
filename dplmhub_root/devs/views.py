from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework import permissions
from django.contrib.auth.models import User
from .serializers import *
from .models import Device, Endpoint
from .domain.interfaces import get_mqttgate_factory
from decouple import config
import json
import functools
from rest_framework import exceptions

class DeviceListApiView(generics.ListCreateAPIView):
    # add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer

    def get_queryset(self):
        user_query = User.objects \
            .filter(pk=self.request.user.pk)
        for user in user_query:
            devmas_query = user.device_masters.all()
            for dev in devmas_query:
                return dev.devices.all()


class DeviceApiView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user_query = User.objects \
            .filter(pk=self.request.user.pk)
        for user in user_query:
            devmas_query = user.device_masters.all()
            for dev in devmas_query:
                return dev.devices.all()


class EndpointApiView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EndpointSerializer

    def get_queryset(self):
        user_query = User.objects \
            .filter(pk=self.request.user.pk)
        for user in user_query:
            devmas_query = user.device_masters.all()
            for dev in devmas_query:
                devices = dev.devices.filter(id=int(self.kwargs['device_pk']))
                for device in devices:
                    return device.endpoints.all()


class EndpointCreateApiView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EndpointSerializer


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
        if devices.count() > 0:
            for device in devices:
                device.wifi_ssid = ''
                device.save()
                get_mqttgate_factory().get_instance().set_network(
                    device.clientID,
                    device.wifi_ssid, device.local_address,
                    validated_data['wifi_ssid'], validated_data['wifi_pass'])
                # we need to send it once, and for every device value will be changed
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)


def action_on_object_validated():
    def inner(action_func):
        @functools.wraps(action_func)
        def wrapper(self, request: Request, *args, **kwargs):
            devices = Device.objects\
                .filter(id=kwargs['device_pk'])
            endpoint = Endpoint.objects.filter(name=kwargs['endpoint'])
            if devices.count() == 0 or endpoint.count() == 0:
                raise exceptions.NotFound(
                    detail="No device or endpoint found")
            payload = ""
            if request.stream is not None:
                payload = bytes(request.stream.read())
            data = {
                'payload': payload,
                'clientID': devices.first().clientID,
                'endpoint': endpoint.first().name
            }
            response_data = action_func(
                self,
                data)
            if response_data is None:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_200_OK, data=response_data)
        return wrapper
    return inner


class DeviceActionView(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    response_serializer = DeviceReadLogSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)

    def get_client_reading(self, clientID: str, endpoint: str):
        user = self.get_queryset().first()
        dev_master = user.device_masters.all().first()
        device = dev_master.devices.filter(clientID=clientID).first()
        endpoint_instance = Endpoint.objects.filter(name=endpoint, device=device.id).first()
        readings_query = device.readings.filter(endpoint=endpoint_instance.id)
        if readings_query:
            return readings_query.latest('read_time')
        return None

    def _get_serializer(self, *args, **kwargs):
        return self.response_serializer(*args, **kwargs)

    @action(["post"], detail=False)
    @action_on_object_validated()
    def dev_read(self, data):
        """ Returns last received reading, published request for a new one """
        readings = self.get_client_reading(data['clientID'], data['endpoint'])
        get_mqttgate_factory()\
            .get_instance()\
            .dev_read(data['endpoint'],
                      data['clientID'])
        if readings is not None:
            return bytes(readings.bin_data)

    @action(["post"], detail=False)
    @action_on_object_validated()
    def dev_put(self, data):
        get_mqttgate_factory()\
            .get_instance()\
            .dev_put(data['endpoint'],
                     data['clientID'],
                     data['payload'])

    @action(["put"], detail=False)
    @action_on_object_validated()
    def dev_update(self, data):
        get_mqttgate_factory()\
            .get_instance()\
            .dev_update(data['endpoint'],
                        data['clientID'],
                        data['payload'])


class ReadLogListView(generics.ListAPIView):
    serializer_class = DeviceReadLogSerializer
    permission_classes = [permissions.AllowAny]
    queryset = DeviceReadLog.objects.all()


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
    """ Returns url to broker network """
    def get(self, request: Request, *args, **kwargs):
        url = os.environ.get("URL_BROKER_NETWORK")
        port = os.environ.get("BROKER_PORT_TLS")
        data = json.dumps((url, port))
        return Response(
            data = str(data),
            status=status.HTTP_200_OK)

