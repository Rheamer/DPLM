from django.dispatch import receiver
import djoser.signals as signals
from .models import DeviceMaster


@receiver(signals.user_registered)
def registrate_device_master(**kwargs):
    master = DeviceMaster()
    master.user = kwargs['user'].id
    master.can_read = True
    master.can_write = True
    master.can_subscribe = True
    master.save()

