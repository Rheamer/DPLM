from . import views
from django.urls import path, include
from .mqtt_client import MqttClient
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register("", views.DeviceActionView, basename='action')

urlpatterns = [
    path('', include(router.urls)),
    path('list', views.DeviceListApiView.as_view(), name='devices'),
    path('<int:id>', views.DeviceApiView.as_view(), name='detail'),
    path('network', views.DeviceNetApiView.as_view(), name='network'),
    path('grids', views.GridListView.as_view(), name='grids')
    # path('devices/create', DeviceConfigUpdateView.as_view(), name = 'creation')
]

