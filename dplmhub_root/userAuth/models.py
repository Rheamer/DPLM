from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class DeviceMaster(models.Model):
    user = models.ForeignKey(User, related_name='master', on_delete=models.PROTECT)
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    can_subscribe = models.BooleanField(default=False)
  
    def __str__(self):
        return self.user

