from rest_framework import serializers
from .models import DeviceMaster
from devs import serializers as dev_serials


class DeviceMasterSerializer(serializers.ModelSerializer):
    devices = dev_serials.DeviceSerializer(many=True)
    class Meta:
        model = DeviceMaster
        fields = '__all__'


class AuthMosquittoSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class AclMosquittoSerializer(serializers.Serializer):
    username = serializers.CharField()
    clientid = serializers.CharField()
    topic = serializers.CharField()
    access = serializers.IntegerField()
