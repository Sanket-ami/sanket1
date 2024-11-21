from django.db import models
from django.utils import timezone
from provider.models import Provider
from voice.models import Voice

class Agent(models.Model):
    agent_name = models.CharField(max_length=255)
    agent_configuration = models.JSONField()  # Django has a JSONField for JSON data
    agent_provider = models.ForeignKey(Provider, on_delete=models.SET_NULL,null=True,related_name="llm")  # FK, quoted as the table doesn't exist yet
    agent_telephony = models.ForeignKey(Provider, on_delete=models.SET_NULL,null=True,related_name="telephony")
    agent_prompt = models.TextField(null=True)
    organisation_name = models.CharField(max_length=255)
    voice = models.ForeignKey(Voice, on_delete=models.SET_NULL,null=True)  # FK, quoted as the table doesn't exist yet
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255,default='SYSTEM',null=True)
    modified_by = models.CharField(max_length=255,default='SYSTEM',null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'agent'  # explicit DB table name

    def __str__(self):
        return self.agent_name
