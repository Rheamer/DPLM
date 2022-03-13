from rest_framework.test import \
    APITestCase, \
    force_authenticate,\
    APIRequestFactory

from rest_framework import status

from django.urls import reverse
from django.contrib.auth.models import User
# import dplmhub_root.devs.models as models
# from .serializers import *
# from .models import *
# from .views import *
from devs import serializers as serials
from devs import models
from devs import views
from userAuth import models as userModels
from userAuth import serializers as userSerials
# Create your tests here.
class TestDeviceView(APITestCase):
    factory = APIRequestFactory()
    view_list = views.DeviceListApiView

    def test_list(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        request = self.factory.get(reverse('devices'))
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        self.assertEqual(resp.status_code, 200)

    def test_create_resp(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        data = {'user': master.id,
                'clientID': 'client'
                }
        serializer = serials.DeviceSerializer(data=data)
        serializer.is_valid()
        # print(f'Serializer is valid? - {serializer.is_valid()}')
        # print(serializer.data)
        request = self.factory.post(reverse('devices'),
                                    data=serializer.data)
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        # print(f'Status - {resp.status_code} {resp.data}')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_resp_data(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        data = {'user': master.id,
                'clientID': 'client'
                }
        serializer = serials.DeviceSerializer(data=data)
        serializer.is_valid()
        # print(f'Serializer is valid? - {serializer.is_valid()}')
        # print(serializer.data)
        request = self.factory.post(reverse('devices'),
                                    data=serializer.data)
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        resp_serializer = serials.DeviceSerializer(data=resp.data)
        resp_serializer.is_valid()
        self.assertEqual(serializer.data['user'], resp_serializer.data['user'])
        self.assertEqual(serializer.data['clientID'], resp_serializer.data['clientID'])

    def test_device_model_create(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        device = models.Device.objects.create(user=master)
        serializer = serials.DeviceSerializer(device, many=False)
        object = models.Device.objects.filter(id=device.id)
        q_serializer = serials.DeviceSerializer(object[0], many=False)
        assert serializer.data == q_serializer.data

