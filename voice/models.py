from django.db import models
from provider.models import Provider

class Voice(models.Model):
    voice_name= models.CharField(max_length=255,null=True) # adding voice name field
    voice_id= models.CharField(max_length=255)
    voice_provider=models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    oragnisation_name=models.CharField(max_length=255)
    voice_configuration=models.CharField(max_length=255)
    create_at=models.DateTimeField(auto_now_add=True)
    modified_at=models.DateTimeField(auto_now=True)
    is_delete=models.BooleanField(default=False)
    created_by = models.CharField(max_length=255, null=True,default='SYSTEM')
    modified_by = models.CharField(max_length=255, null=True,default='SYSTEM')
    
    class Meta:
        db_table = 'voice'  

    def __str__(self):
        return self.voice_id