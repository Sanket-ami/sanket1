from django.db import models


class Provider(models.Model):
    provider_name=models.CharField(max_length=255)
    provider_config=models.CharField(max_length=255)  #json
    is_delete=models.JSONField()
    
    class Meta:
        db_table = 'provider'  

    def __str__(self):
        return self.provider_name