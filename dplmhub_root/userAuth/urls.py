
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from .views import *
from .utils import *

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('devreg', AuthMosquittoView.as_view(), name='mosq-api-auth'),
    path('acl', AclMosquittoView.as_view(), name='mosq-acl')
]
