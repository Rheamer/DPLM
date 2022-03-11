from rest_framework.test import APITestCase, force_authenticate
from rest_framework.test import APIRequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
# import dplmhub_root.devs.models as models
# from .serializers import *
# from .models import *
# from .views import *
from devs import serializers as serials
from devs import models
from devs import views


# Create your tests here.
class TestDeviceView(APITestCase):
    factory = APIRequestFactory()
    user = User.objects.get(username='olivia')

    def test_list(self):
        force_authenticate(user=self.user)
        resp = self.client.get(reverse('devices'))
        self.assertEqual(resp.status_code, 200)

    def test_create_resp(self):
        data = {'user': 0,
                'clientID': 'client',
                'grid': 0}
        serializer = serials.DeviceSerializer(data=data)
        req = APIRequestFactory().post(path=reverse('devices'),
                                    data=serializer.data)
        resp = views.DeviceListApiView.as_view()(req)
        assert resp.status_code == 200

    def test_create_resp_data(self):
        data = {'user': 0,
                'clientID': 'client',
                'grid': 0}
        serializer = serials.DeviceSerializer(data=data)
        req = APIRequestFactory().post(path=reverse('devices'),
                                    data=serializer.data)
        resp = views.DeviceListApiView.as_view()(req)
        resp_serializer = serials.DeviceSerializer(data=resp.data)
        assert serializer.data == resp_serializer.data

    def test_create_query(self):
        data = {'user': 0,
                'clientID': 'client',
                'grid': 0}
        serializer = serials.DeviceSerializer(data=data)
        req = APIRequestFactory().post(path=reverse('devices'),
                                    data=serializer.data)
        object = models.Device.objects.filter(clientID='client')
        q_serializer = serials.DeviceSerializer(object, many=False)
        assert serializer.data == q_serializer.data

