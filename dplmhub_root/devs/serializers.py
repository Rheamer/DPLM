from rest_framework import serializers
from .models import Device, Grid, DeviceReadLog
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
    clientID = serializers.CharField()
    payload = serializers.CharField()
    endpoint = serializers.CharField()

    def get_filter_field(self):
        return self.data['clientID']

    # class Meta:
    #     model = DeviceReadLog
    #     fields = ['value', 'endpoint', 'clientID']
