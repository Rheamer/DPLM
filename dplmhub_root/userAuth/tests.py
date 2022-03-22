from rest_framework.test import \
    APITestCase, \
    force_authenticate,\
    APIRequestFactory
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from .views import AuthMosquittoView, AclMosquittoView
from .serializers import AclMosquittoSerializer, AuthMosquittoSerializer
from .models import DeviceMaster
from devs.models import Device

class TestUserView(APITestCase):
    factory = APIRequestFactory()
    view = AuthMosquittoView
    multi_db = True

    def test_registration(self):
        data = {
            'email': 'test@gmail.com',
            'username': 'test_name',
            'password': 'test_password'
        }
        resp = self.client.post('http://127.0.0.1:8000/auth/users/', data=data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, msg=str(resp))

    def test_master_creation_signal(self):
        data = {
            'email': 'test@gmail.com',
            'username': 'test_name',
            'password': 'test_password'
        }
        resp = self.client.post('http://127.0.0.1:8000/auth/users/', data=data)
        user_query = User.objects.filter(username='test_name')
        self.assertGreater(user_query.count(), 0)
        user = user_query[0]
        self.assertGreater(user.device_masters.all().count(), 0,
                           msg='Device master created whilst preping the view')


class TestMosquittoView(APITestCase):
    factory = APIRequestFactory()
    view = AclMosquittoView
    multi_db = True

    def test_acl_subscribe(self):
        # Create user
        user = User.objects.create_user(username='test_name', password='test_password')
        dev_master = DeviceMaster.objects.create(user=user, can_read=True)
        device = Device.objects.create(user=dev_master, clientID='test_clientid')
        data = {
            'username': 'test_name',
            'clientid': 'test_clientid',
            'topic': 'test_topic/test_clientid/test_endpoint',
            'access': '1'
        }
        serializer = AclMosquittoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        resp = self.client.post(
            reverse('mosq-acl'),
            data=serializer.validated_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_acl_subscribe_no_device(self):
        # Create user
        user = User.objects.create_user(username='test_name', password='test_password')
        dev_master = DeviceMaster.objects.create(user=user, can_write=False)
        device = Device.objects.create(user=dev_master, clientID='test_clientid')
        data = {
            'username': 'test_name',
            'clientid': 'test_clientid',
            'topic': 'test_topic/test_clientid/test_endpoint',
            'access': '2'
        }
        serializer = AclMosquittoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        resp = self.client.post(
            reverse('mosq-acl'),
            data=serializer.validated_data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_acl_subscribe_bad_topic(self):
        # Create user
        user = User.objects.create_user(username='test_name', password='test_password')
        dev_master = DeviceMaster.objects.create(user=user, can_write=False)
        device = Device.objects.create(user=dev_master, clientID='test_clientid')
        data = {
            'username': 'test_name',
            'clientid': 'test_client2',
            'topic': 'test_topic/test_clientid/test_endpoint',
            'access': '2'
        }
        serializer = AclMosquittoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        resp = self.client.post(
            reverse('mosq-acl'),
            data=serializer.validated_data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_auth(self):
        user = User.objects.create_user(username='test_name', password='test_password')
        data = {
            'username': 'test_name',
            'password': 'test_password',
        }
        serializer = AuthMosquittoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        resp = self.client.post(
            reverse('mosq-api-auth'),
            data=serializer.validated_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_auth_unauthorized(self):
        data = {
            'username': 'test_name',
            'password': 'test_password',
        }
        serializer = AuthMosquittoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        resp = self.client.post(
            reverse('mosq-api-auth'),
            data=serializer.validated_data)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
