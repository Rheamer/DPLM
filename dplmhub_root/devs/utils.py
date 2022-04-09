from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
import functools
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework import exceptions
from .models import Device
from abc import ABC, abstractmethod
from rest_framework import serializers

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.default_code
    return response


class DeviceException(APIException):
    pass


class FilterableSerializer(serializers.Serializer):

    @abstractmethod
    def get_filter_field(self):
        pass


def action_on_object_validated(filtered_model):
    def inner(action_func):
        @functools.wraps(action_func)
        def wrapper(self, request: Request, *args, **kwargs):
            devices = filtered_model.objects\
                .filter(id=kwargs['device_pk'])
            if devices.count() == 0:
                raise exceptions.APIException(
                    detail="No device found")
            payload = bytes(request.stream.read())
            data = {
                'payload': payload,
                'clientID': devices.first().clientID,
                'endpoint': kwargs['endpoint']
            }
            response_data = action_func(
                self,
                data)
            if data is None:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_200_OK, data=response_data)
        return wrapper
    return inner
