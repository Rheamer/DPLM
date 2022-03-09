from rest_framework import serializers
from .models import DeviceMaster
class DeviceMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceMaster
        fields = ['user', 'car_read', 'can_write', 'can_subscribe']