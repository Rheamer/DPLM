from django.contrib import admin
from .models import Device
from .models import Grid

class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'clientID', 
        'local_address', 
        'wifi_ssid')

class GridAdmin(admin.ModelAdmin):
    list_user = ('user')
    list_broker_name = ('broker_name')

admin.site.register(Device, DeviceAdmin)
admin.site.register(Grid, GridAdmin)
