from rest_framework.views import exception_handler
from abc import ABC, abstractmethod
from rest_framework import serializers

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.default_code
    return response


class FilterableSerializer(serializers.Serializer):

    @abstractmethod
    def get_filter_field(self):
        pass
