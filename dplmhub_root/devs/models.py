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
    broker_name = models.CharField(max_length=100, default="Default Broker")
    broker_address = models.CharField(max_length=40, default="", blank=True)
    wifi_ssid = models.CharField(max_length=100, default='DPLM_BaseNetwork')

    def __str__(self):
        return self.broker_name


class Device(models.Model):
    user = models.ForeignKey(
        DeviceMaster,
        related_name='devices',
        on_delete=models.CASCADE
    )
    clientID = models.CharField(max_length=100, unique=True, db_index=True)
    local_address = models.CharField(max_length=40, default='127.0.0.1')
    last_update = models.DateTimeField(auto_now=True)
    wifi_ssid = models.CharField(max_length=100, default='DPLM_BaseNetwork')
    can_read = models.BooleanField(default=False)
    grid = models.ForeignKey(
        Grid,
        related_name='device',
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    def __str__(self):
        return self.clientID


class DeviceReadLog(models.Model):
    device = models.ForeignKey(Device,
                               related_name='readings',
                               on_delete=models.CASCADE)
    data = models.BinaryField(max_length=16384)
    endpoint = models.CharField(max_length=100)
    read_time = models.DateTimeField(auto_now=True)


class Endpoint(models.Model):
    device = models.ForeignKey(
        Device,
        related_name='endpoints',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    io_type = models.CharField(max_length=30)
    data_type = models.CharField(max_length=30)
