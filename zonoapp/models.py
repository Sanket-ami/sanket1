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

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status_balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    call_rate = models.DecimalField(max_digits=10, decimal_places=2, default=10, null=True)  # Avoid division by zero
    status_rate = models.DecimalField(max_digits=10, decimal_places=2, default=10, null=True)

    calls_threshold = models.IntegerField(default=3)

    def save(self, *args, **kwargs):
        if self.balance != 0:
            self.credits = (self.balance  / self.call_rate) * 100
        else:
            self.credits = 0  

        if self.balance != 0:
            self.status_balance = (self.balance  / self.status_rate) * 100
        else:
            self.status_balance = 0  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Account {self.id} - Balance: {self.balance}, Call Balance: {self.call_balance}"


class PaymentStatus(models.Model):
    organisation_name=models.CharField(max_length=255)
    user_id=models.IntegerField()
    status=models.CharField(max_length=255)
    amount=models.IntegerField()
    payment_response=models.CharField(max_length=255)
