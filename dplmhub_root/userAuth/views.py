from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.contrib.auth.models import User
from .serializers import AclMosquittoSerializer, AuthMosquittoSerializer
from rest_framework import permissions
from django.contrib.auth import authenticate
from rest_framework import generics


class ValidateDataMixin():
    def get_validated_data(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(request.data)
        serializer.is_valid(raise_exceptions=True)
        return serializer.validated_data


# Create your views here.
class AclMqttView(generics.GenericAPIView, ValidateDataMixin):
    permission_classes = [permissions.AllowAny]
    serializer_class = AclMosquittoSerializer

    def post(self, request: Request, *args, **kwargs):
        acl_request = self.get_validated_data(request)
        if acl_request['topic'] == 'discovery/registration':
            return Response(status=status.HTTP_200_OK)

        user = User.objects.filter(username=acl_request['username']).get(0)
        device_master = user.device_masters.objects.all().get(0)
        device = device_master.devices.objects\
            .filter(clientID=acl_request['clientid'])

        if device.count() < 1:
            return Response(status=status.HTTP_403_FORBIDDEN)

        access = acl_request['access']
        if access == 1 or access == 4:  # subscribe and read is the same
            if device_master.can_read:
                return Response(status=status.HTTP_200_OK)

        if access == 2 or access == 3:  # write and read/write
            if device_master.can_write:
                return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_403_FORBIDDEN)


class AuthMqttView(generics.GenericAPIView, ValidateDataMixin):
    permission_classes = [permissions.AllowAny]
    serializer_class = AuthMosquittoSerializer

    def post(self, request: Request, *args, **kwargs):
        auth_request = self.get_validated_data(request)
        user = authenticate(username=auth_request['username'],
                            password=auth_request['password'])
        if user is not None:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
