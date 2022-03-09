from http import client
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.contrib.auth.models import User
from .models import DeviceMaster
from rest_framework import permissions
from django.contrib.auth import authenticate
from devs.models import Device
# Create your views here.
class AclMqttView(APIView):
    permission_classes = [permissions.AllowAny]
    queryset = DeviceMaster.objects.select_related('User')
    def post(self, request: Request, *args, **kwargs):
        
        _username = request.data.get('username')
        _clientID = request.data.get('clientid')
        _topic = request.data.get('topic')
        _access = request.data.get('acc')

        if _topic == 'discovery/registration':
            return Response( status = status.HTTP_200_OK )

        query = Device.objects.all().filter(clientID = _clientID)\
            .select_related('User')\
            .select_related('User')

        if query.count() != 1:
            return Response( status = status.HTTP_400_NOT_FOUND )

        ## Validate topic!!!!!!!!!!!!
        ## Check by name or clientID, they HAVE to be present for private control

        if _access == 1 or _access == 4: #subscribe and read is the same
            if query[0].can_read:
                return Response( status = status.HTTP_200_OK )
        
        if _access == 2 or _access == 3: #write and read/write 
            return Response( status = status.HTTP_200_OK )

        return Response( status = status.HTTP_400_NOT_FOUND ) 

class AuthMqttView(APIView):
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.filter()
    def post(self, request: Request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            return Response( status = status.HTTP_200_OK )
        else:
            return Response( status = status.HTTP_400_NOT_FOUND ) 

