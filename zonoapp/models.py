# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    organisation_name = models.CharField(max_length=255, blank=False)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL,null=True)
    is_deleted = models.BooleanField(default=True)
    def __str__(self):
        return self.username

class Role(models.Model):
    role = models.CharField(max_length=255, blank=False)
    organisation_name = models.CharField(max_length=255, blank=False)
    is_deleted = models.BooleanField(default=True)
    
    class meta:
        db_table = "role"
    def __str__(self):
        return self.role