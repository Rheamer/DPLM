from rest_framework import serializers
from .models import Device, Grid, DeviceReadLog, Endpoint
from .utils import FilterableSerializer



class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class GridSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grid
        fields = '__all__'


class NetworkSwitchSerializer(serializers.Serializer):
    old_wifi_ssid = serializers.CharField(max_length=100)
    wifi_ssid = serializers.CharField(max_length=100)
    wifi_pass = serializers.CharField(max_length=100)


class DeviceActionSerializer(FilterableSerializer):
    """ DEPRECATED """
    clientID = serializers.CharField()
    payload = serializers.CharField(allow_blank=True, default=None)
    endpoint = serializers.CharField()

    def get_filter_field(self):
        return self.data['clientID']


class DeviceReadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceReadLog
        fields = '__all__'


class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = '__all__'

