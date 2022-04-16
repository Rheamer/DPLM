from rest_framework.test import \
    APITestCase, \
    force_authenticate,\
    APIRequestFactory

from rest_framework import status

from django.urls import reverse
from django.contrib.auth.models import User
from devs import serializers as serials
from devs import models
from devs import views
from userAuth import models as userModels
import base64


class TestDeviceView(APITestCase):
    factory = APIRequestFactory()
    view_list = views.DeviceListApiView
    view_detail = views.DeviceApiView
    multi_db = True

    def test_list(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        request = self.factory.get(reverse('devices'))
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        self.assertEqual(resp.status_code, 200)

    def test_detail(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        device = models.Device.objects.create(user=master, clientID='test_clientID')
        request = self.factory.get(reverse('detail', args=(device.id,)))
        force_authenticate(request, user=user)
        resp = self.view_detail.as_view()(request, id=device.id)
        self.assertEqual(resp.status_code, 200, msg=resp.data)
        self.assertEqual(resp.data['clientID'], device.clientID)

    def test_create_resp(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        data = {'user': master.id,
                'clientID': 'test_client'
                }
        serializer = serials.DeviceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        request = self.factory.post(reverse('devices'),
                                    data=data)
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_resp_data(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        data = {'user': master.id,
                'clientID': 'test_client'
                }
        serializer = serials.DeviceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        request = self.factory.post(reverse('devices'),
                                    data=data)
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
        self.assertEqual(serializer.data, q_serializer.data)

    
class TestGridAPI(APITestCase):
    factory = APIRequestFactory()
    view_list = views.GridListView
    multi_db = True

    def test_get_grid_response(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        request = self.factory.get(reverse('grids'))
        models.Grid.objects.create(user=master)
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_grid_validation(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        request = self.factory.get(reverse('grids'))
        models.Grid.objects.create(user=master)
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        for data in resp.data:
            serializer = serials.GridSerializer(data=data, many=False)
            self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_get_grid_master(self):
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        request = self.factory.get(reverse('grids'))
        models.Grid.objects.create(user=master)
        force_authenticate(request, user=user)
        resp = self.view_list.as_view()(request)
        for data in resp.data:
            serializer = serials.GridSerializer(data=data, many=False)
            serializer.is_valid(raise_exception=True)
            self.assertEqual(serializer.data['user'], master.id)


class TestDeviceActionAPI(APITestCase):
    factory = APIRequestFactory()
    view = views.DeviceActionView
    multi_db = True

    def test_no_device_action(self):
        # No device is supposed to be found
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')

        request = self.factory.post(
            reverse(
                'action-dev-put',
                args=(0, 'test_endpoint',)
            )
        )
        force_authenticate(request, user=user)
        resp = self.view.as_view({'post': 'dev_put'})(request,
                                                      device_pk=0,
                                                      endpoint='test_endpoint')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_action(self):
        # Wrapper test
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        device = models.Device.objects.create(user=master, clientID='test_clientID')
        endpoint = models.Endpoint.objects.create(
            device=device,
            name='test_endpoint',
            io_type='0',
            data_type='0'
        )
        request = self.factory.post(
            reverse(
                'action-dev-put',
                args=(device.id, 'test_endpoint',)
            ),
            data=b'test',
            content_type="text/plain"
        )
        force_authenticate(request, user=user)
        resp = self.view.as_view({'post': 'dev_put'})(request,
                                                      device_pk=device.id,
                                                      endpoint='test_endpoint')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


    def test_action_read(self):
        # Wrapper test
        user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
        master = userModels.DeviceMaster.objects.create(user=user)
        device = models.Device.objects.create(user=master, clientID='test_clientID')
        endpoint = models.Endpoint.objects.create(
            device=device,
            name='test_endpoint',
            io_type='0',
            data_type='0'
        )
        readlog = models.DeviceReadLog \
            .objects.create(device=device,
                            bin_data=bytes('testest', 'utf-8'),
                            endpoint=endpoint)
        request = self.factory.post(
            reverse(
                'action-dev-read',
                args=(device.id, 'test_endpoint',)
            ),
        )
        force_authenticate(request, user=user)
        resp = self.view.as_view({'post': 'dev_read'})(request,
                                                       device_pk=device.id,
                                                       endpoint='test_endpoint')
        self.assertIsNotNone(resp.data)
        self.assertEqual(
            resp.data,
            readlog.bin_data)


    # TODO: other action tests

    # def test_update(self):
    #     user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
    #
    # def test_put(self):
    #     user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')
    #
    # def test_read(self):
    #     user = User.objects.create_user('Test1', 'Test@gmail.com', 'TestPass')

