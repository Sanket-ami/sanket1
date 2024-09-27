from django.db import models
from provider.models import Provider
from agent.models import Agent
# Create your models here.

class Campaign(models.Model):
    campaign_name = models.CharField(max_length=255, blank=False)
    is_schedule = models.BooleanField(default=True)
    organisation_name = models.CharField(max_length=255, blank=False)
    show_transcript = models.BooleanField(default=False)
    process_type = models.CharField(max_length=255, blank=False)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True)
    show_recording = models.BooleanField(default=True)
    show_numbers = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, null=True,default='SYSTEM')
    modified_by = models.CharField(max_length=255, null=True,default='SYSTEM')
    is_delete=models.BooleanField(default=False)
    class meta:
        db_table = "campaign"
    def __str__(self):
        return self.campaign_name
    


 