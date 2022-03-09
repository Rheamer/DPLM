from django.contrib import admin
from .models import DeviceMaster
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('user','can_write', 'can_subscribe')

admin.site.register(DeviceMaster, UserAdmin)