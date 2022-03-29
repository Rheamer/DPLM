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
        def wrapper(self, request: Request):
            serializer: FilterableSerializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            devices = filtered_model.objects\
                .filter(clientID=serializer.get_filter_field())
            if devices.count() == 0:
                raise exceptions.NotFound(
                    detail="No device with provided ID")
            data = action_func(
                self,
                serializer.validated_data)
            if data is None:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_200_OK, data=data)
        return wrapper
    return inner
