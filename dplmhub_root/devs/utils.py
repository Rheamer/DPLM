from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
import functools
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework import exceptions
from .models import Device

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.default_code
    return response


class DeviceException(APIException):
    pass


def action_validation_wrapper(action_func):
    @functools.wraps(action_func)
    def wrapper(self, request: Request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        devices = Device.objects\
            .filter(clientID=serializer.data['clientID'])
        if devices.count() == 0:
            raise exceptions.NotFound(
                detail="No device with provided ID")
        action_func(
            self,
            endpoint=serializer.data['endpoint'],
            clientID=serializer.data['clientID'],
            payload=serializer.data['payload'])
        return Response(status=status.HTTP_200_OK)
    return wrapper
