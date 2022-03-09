import imp
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from .views import *

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('devconnect', AuthMqttView.as_view(), name = 'mosq-api-auth'),
    path('acl', AclMqttView.as_view(), name = 'mosq-acl')
]
