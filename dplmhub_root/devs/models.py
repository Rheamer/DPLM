from datetime import date
from django.db import models
from enum import Enum
from userAuth.models import DeviceMaster


# Grid is defined by local broker
class Grid(models.Model):
    user = models.ForeignKey(
        DeviceMaster,
        related_name='grids',
        on_delete=models.PROTECT)
    broker_address = models.CharField(max_length=40, default="", blank=True)
    wifi_ssid = models.CharField(
        max_length=100,
        blank=True,
        default=None,
        db_index=True)
    def __str__(self):
        return self.wifi_ssid


class Device(models.Model):
    user = models.ForeignKey(
        DeviceMaster,
        related_name='devices',
        on_delete=models.CASCADE
    )
    clientID = models.CharField(max_length=100, unique=True, db_index=True)
    local_address = models.CharField(max_length=40, default='127.0.0.1')
    last_update = models.DateTimeField(auto_now=True)
    grid = models.ForeignKey(
        Grid,
        related_name='devices',
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    def __str__(self):
        return self.clientID


class Endpoint(models.Model):
    device = models.ForeignKey(
        Device,
        related_name='endpoints',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100,
                            db_index=True)
    io_type = models.CharField(max_length=30)
    data_type = models.CharField(max_length=30)


class DeviceReadLog(models.Model):
    device = models.ForeignKey(Device,
                               related_name='readings',
                               on_delete=models.PROTECT)
    bin_data = models.BinaryField(max_length=16384)
    """ 
    Endpoint can be deleted at any point. 
    Device fk is needed to avoid dangling readings 
    """
    endpoint = models.ForeignKey(Endpoint,
                                 related_name='readings',
                                 on_delete=models.SET_NULL,
                                 blank=True,
                                 null=True)
    read_time = models.DateTimeField(auto_now=True)
