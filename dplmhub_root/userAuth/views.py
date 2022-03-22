from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.contrib.auth.models import User
from .serializers import AclMosquittoSerializer, AuthMosquittoSerializer
from rest_framework import permissions
from django.contrib.auth import authenticate
from rest_framework import generics
from rest_framework import exceptions
from .utils import is_valid_topic

class ValidateDataMixin:
    def get_validated_data(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


# Create your views here.
class AclMosquittoView(generics.GenericAPIView, ValidateDataMixin):
    permission_classes = [permissions.AllowAny]
    serializer_class = AclMosquittoSerializer

    def post(self, request: Request, *args, **kwargs):
        acl_request = self.get_validated_data(request)
        if acl_request['topic'] == 'discovery/registration':
            return Response(status=status.HTTP_200_OK)
        user_query = User.objects.filter(username=acl_request['username'])
        if user_query.count() < 1:
            raise exceptions.NotFound()
        user = user_query[0]
        device_master = user.device_masters.all()[0]
        device = device_master.devices\
            .filter(clientID=acl_request['clientid'])
        if device.count() < 1:
            raise exceptions.PermissionDenied('No such devices are registered')

        # Topic validation: should have client ID
        if not is_valid_topic(topic=acl_request['topic'],
                              clientID=acl_request['clientid']):
            raise exceptions.PermissionDenied('No permission for this topic')

        access = acl_request['access']
        if access == 1 or access == 4:  # subscribe and read is the same
            if device_master.can_read:
                return Response(status=status.HTTP_200_OK)

        if access == 2 or access == 3:  # write and read/write
            if device_master.can_write:
                return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_403_FORBIDDEN)


class AuthMosquittoView(generics.GenericAPIView, ValidateDataMixin):
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
