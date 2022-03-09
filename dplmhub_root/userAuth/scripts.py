from django.dispatch import receiver
import djoser.signals as signals
from .serializers import DeviceMasterSerializer

@receiver(signals.user_registered)
def RegistrateDeviceMaster(**kwargs):
    data = {
        'user': kwargs['user'].id,
        'can_read': True,
        'can_write': True,
        'can_subscribe': True
    }
    serializer = DeviceMasterSerializer(data = data)
    if serializer.is_valid():
        serializer.save()

