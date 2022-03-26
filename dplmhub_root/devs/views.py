from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework import permissions
from django.contrib.auth.models import User
from .serializers import *
from .domain.interfaces import get_gateway_factory
from decouple import config
from .utils import action_on_object_validated, FilterableSerializer


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
        if devices.count() > 0:
            for device in devices:
                get_gateway_factory().get_instance().set_network(
                    device.wifi_ssid, device.local_address,
                    validated_data['wifi_ssid'], validated_data['wifi_pass'])
                # we need to send it once, and for every device value will be changed
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_NOT_FOUND)


class DeviceActionView(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceActionSerializer
    response_serializer = DeviceReadLogSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)

    def get_client_reading(self, clientID: str):
        user = self.get_queryset()[0]
        dev_master = user.device_masters.all().first()
        device = dev_master.devices.filter(clientID=clientID).first()
        return device.readings.latest('read_time')

    def get_serializer(self, *args, **kwargs) -> FilterableSerializer:
        return self.serializer_class(*args, **kwargs)

    @action(["post"], detail=False)
    @action_on_object_validated(Device)
    def dev_read(self, data):
        """ Returns last received reading, published request for a new one """
        get_gateway_factory()\
            .get_instance()\
            .dev_read(data['endpoint'],
                      data['clientID'])
        readings = self.get_client_reading(data['clientID'])
        if readings is not None:
            serializer = self.\
                response_serializer(readings,
                                    many=False)
            return serializer.data

    @action(["post"], detail=False)
    @action_on_object_validated(Device)
    def dev_put(self, data):
        get_gateway_factory()\
            .get_instance()\
            .dev_put(data['endpoint'],
                     data['clientID'],
                     data['payload'])

    @action(["put"], detail=False)
    @action_on_object_validated(Device)
    def dev_update(self, data):
        get_gateway_factory()\
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
        return Response(
            data=config("URL_BROKER_NETWORK"),
            status=status.HTTP_200_OK)

