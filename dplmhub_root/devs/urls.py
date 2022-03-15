import threading
from . import views
from django.urls import path, include
from .mqtt_server import MqttServer
from rest_framework.routers import DefaultRouter


mqtt = MqttServer.getInstance()

router = DefaultRouter()
router.register("", views.DeviceActionView, basename='action')

urlpatterns = router.urls + [
    path('list', views.DeviceListApiView.as_view(), name='devices'),
    # TODO: implement: identify in url by id
    # path('devices/<int:id>', DeviceListApiView.as_view(), name='devices'),
    path('network', views.DeviceNetApiView.as_view(), name='network'),
    # path('devices/action', DeviceActionView.as_view(), name='action'),
    path('grids', views.GridListView.as_view(), name='grids')
    # path('devices/create', DeviceConfigUpdateView.as_view(), name = 'creation')
]


# TODO: implement as process, not thread
# threading.Thread(target=mqtt.run_mqtt_server).start()
