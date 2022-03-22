from django.dispatch import receiver
import djoser.signals as signals
from .models import DeviceMaster


@receiver(signals.user_registered)
def registrate_device_master(*args, **kwargs):
    master = DeviceMaster()
    master.user = kwargs['user']
    master.can_read = True
    master.can_write = True
    master.can_subscribe = True
    master.save()


def is_valid_topic(topic: str, clientID: str):
    """ Only valid if topic are delimited by '/' """
    start_index = topic.find(clientID)
    try:
        if topic[start_index-1] == '/' and \
                topic[start_index+len(clientID)] == '/':
            return True
    except IndexError:
        return False
    finally:
        return False
