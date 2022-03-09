import threading
from . import views
from django.urls import path, include
from . views import *
from .mqtt_server import MqttServer
mqtt = MqttServer.getInstance()
urlpatterns = [
    path('devices', DeviceListApiView.as_view(), name='devices'),
    # TODO: implement: identify in url by id
    # path('devices/<int:id>', DeviceListApiView.as_view(), name='devices'),
    path('devices/network', DeviceNetApiView.as_view(), name='devices'),
    path('devices/action', DeviceActionView.as_view(), name='action'),
    path('grids', GridListView.as_view(), name='grids')
    # path('devices/create', DeviceConfigUpdateView.as_view(), name = 'creation')
]
threading.Thread(target=mqtt.run_mqtt_server).start()
