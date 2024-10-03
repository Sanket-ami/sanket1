from django.db import models
from provider.models import Provider
from agent.models import Agent
import mongoengine as me
import datetime
# Create your models here.

class Campaign(models.Model):
    campaign_name = models.CharField(max_length=255, blank=False)
    is_schedule = models.BooleanField(default=True)
    organisation_name = models.CharField(max_length=255, blank=False)
    status=models.CharField(max_length=255, blank=False,default="not_started")
    show_transcript = models.BooleanField(default=False)
    process_type = models.CharField(max_length=255, blank=False)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True)
    contact_list = models.JSONField(default=[],)
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
    
 
class Transcript(models.Model):
    # Assuming the foreign key is pointing to a Campaign model
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True)
    call_logs = models.CharField(max_length=255)  # call_log mongo id
    transcript = models.TextField()
    organisation_name = models.CharField(max_length=255,null=True)  # Assuming VARCHAR has a maximum length
    summary = models.TextField()
    qa_analysis = models.JSONField(default=[])
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255)  # Assuming VARCHAR has a maximum length
    modified_by = models.CharField(max_length=255)  # Assuming VARCHAR has a maximum length
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'transcript'  # Specify the table name if it's different
 

    def __str__(self):
        return self.call_logs  # or any other field you prefer to display


class CallLogs(me.DynamicDocument):
    call_id = me.StringField(required=True)
    created_at = me.DateTimeField(default=datetime.datetime.now())

    meta = {
        'collection': 'calls',  # Optional
        'ordering': ['-created_at']  # Optional
    }
 
