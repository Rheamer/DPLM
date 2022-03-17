from rest_framework import serializers
from .models import DeviceMaster
from devs import serializers as dev_serials


class DeviceMasterSerializer(serializers.ModelSerializer):
    devices = dev_serials.DeviceSerializer(many=True)

    class Meta:
        model = DeviceMaster
        fields = '__all__'
