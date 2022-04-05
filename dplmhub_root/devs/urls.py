from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .domain.interfaces import get_mqttgate_factory

gateway_client_factory = get_mqttgate_factory()
get_mqttgate_factory().get_instance().connect()

router = DefaultRouter()
router.register("", views.DeviceActionView, basename='action')

urlpatterns = [
    path('action/', include(router.urls)),
    path('list', views.DeviceListApiView.as_view(), name='devices'),
    path('<int:id>', views.DeviceApiView.as_view(), name='detail'),
    path('network', views.DeviceNetApiView.as_view(), name='network'),
    path('grids', views.GridListView.as_view(), name='grids'),
    path('endpoints/<int:client_id>', views.EndpointApiView.as_view(), name='endpoints')
]

