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
        related_name='device',
        on_delete=models.PROTECT)
    clientID = models.CharField(max_length=100, unique=True)
    local_address = models.CharField(max_length=40, default='127.0.0.1')
    last_update = models.DateTimeField(auto_now=True)
    wifi_ssid = models.CharField(max_length=100, default='DPLM_BaseNetwork')
    can_read = models.BooleanField(default=False)
    grid = models.ForeignKey(
        Grid,
        related_name='device',
        on_delete=models.PROTECT,
        # TODO: tests fail
        #  TypeError: Cannot encode None for key 'grid' as POST data.
        #  Did you mean to pass an empty string or omit the value?
        #  when  null=True, should be otherwise
        null=True,
        blank=True)

    def __str__(self):
        return self.clientID


class Topic(models.Model):
    user = models.ForeignKey(DeviceMaster, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='')

