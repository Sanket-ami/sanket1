# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    organisation_name = models.CharField(max_length=255, blank=False)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL,null=True)
    is_deleted = models.BooleanField(default=False)
    def __str__(self):
        return self.username

class Role(models.Model):
    role = models.CharField(max_length=255, blank=False)
    is_deleted = models.BooleanField(default=True)
    class meta:
        db_table = "role"
    def __str__(self):
        return self.id

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organisation_name = models.CharField(max_length=255,null=True)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message

# model to store credits of users
class Credits(models.Model):
    credits = models.IntegerField(default=0)
    organisation_name = models.CharField(max_length=255, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, null=True,default='SYSTEM')
    modified_by = models.CharField(max_length=255, null=True,default='SYSTEM')    
    is_deleted = models.BooleanField(default=True)
    class meta:
        db_table = "credits"

class CreditRate(models.Model):
    organisation_name=models.CharField(max_length=255, unique=True)
    rate=models.IntegerField(default=10)
    class meta:
        db_table='credit_rate'

class PaymentStatus(models.Model):
    organisation_name=models.CharField(max_length=255)
    user_id=models.IntegerField()
    status=models.CharField(max_length=255)
    amount=models.IntegerField()
    payment_response=models.CharField(max_length=255)
