from django.db import models


class Provider(models.Model):
    provider_name=models.CharField(max_length=255)
    provider_config=models.JSONField()
    provider_type=models.CharField(max_length=255)
    is_delete=models.CharField(default=False)
    
    
    class Meta:
        db_table = 'provider'  

    def __str__(self):
        return self.provider_name