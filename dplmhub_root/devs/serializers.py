from rest_framework import serializers
from .models import Device, Grid


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

