from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework import permissions
from django.contrib.auth.models import User
from .serializers import *
from .domain.interfaces import get_mqttgate_factory
from decouple import config
from .utils import action_on_object_validated, FilterableSerializer
import json

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


class DeviceActionView(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    response_serializer = DeviceReadLogSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)

    def get_client_reading(self, clientID: str, endpoint):
        user = self.get_queryset()[0]
        dev_master = user.device_masters.all().first()
        device = dev_master.devices.filter(clientID=clientID).first()
        return device.readings.filter(endpoint=endpoint).latest('read_time')

    def _get_serializer(self, *args, **kwargs):
        return self.response_serializer(*args, **kwargs)

    @action(["post"], detail=False)
    @action_on_object_validated(Device)
    def dev_read(self, data):
        """ Returns last received reading, published request for a new one """
        readings = self.get_client_reading(data['clientID'], data['endpoint'])
        get_mqttgate_factory()\
            .get_instance()\
            .dev_read(data['endpoint'],
                      data['clientID'])
        if readings is not None:
            serializer = self.\
                _get_serializer(readings, many=False)
            return serializer.data

    @action(["post"], detail=False)
    @action_on_object_validated(Device)
    def dev_put(self, data):
        get_mqttgate_factory()\
            .get_instance()\
            .dev_put(data['endpoint'],
                     data['clientID'],
                     data['payload'])

    @action(["put"], detail=False)
    @action_on_object_validated(Device)
    def dev_update(self, data):
        get_mqttgate_factory()\
            .get_instance()\
            .dev_update(data['endpoint'],
                        data['clientID'],
                        data['payload'])


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
        url = config("URL_BROKER_NETWORK")
        port = config("BROKER_PORT_TLS")
        data = json.dumps((url, port))
        return Response(
            data = str(data),
            status=status.HTTP_200_OK)

