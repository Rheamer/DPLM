from django.contrib import admin
from .models import *


@admin.register(Device, Endpoint, Grid, DeviceReadLog)
class UniversalAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]
