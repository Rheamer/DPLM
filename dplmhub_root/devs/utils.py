from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.default_code
    return response

class DeviceException(APIException):
    pass