from django.db import models
from provider.models import Provider
from agent.models import Agent
from qa_parameters.models import QAParameters
import mongoengine as me
import datetime
from django.utils import timezone

# Create your models here.

class Campaign(models.Model):
    campaign_name = models.CharField(max_length=255, blank=False)
    is_schedule = models.BooleanField(default=True)
    summarization_prompt = models.TextField(null=True)
    qa_parameters = models.ForeignKey(QAParameters, on_delete=models.SET_NULL, null=True)
    organisation_name = models.CharField(max_length=255, blank=False)
    status=models.CharField(max_length=255, blank=False,default="not_started")
    show_transcript = models.BooleanField(default=False)
    process_type = models.CharField(max_length=255, blank=False)
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True)
    contact_list = models.ForeignKey("ContactList", on_delete=models.SET_NULL, null=True, related_name="campaigns")
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
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True)
    call_logs = models.CharField(max_length=255)  # call_log mongo id
    transcript = models.TextField()
    organisation_name = models.CharField(max_length=255,null=True)  # Assuming VARCHAR has a maximum length
    recording = models.TextField(null=True)
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
 

class ContactList(models.Model):
    list_name = models.CharField(max_length=255)
    campaign = models.ForeignKey("Campaign", on_delete=models.SET_NULL, null=True, related_name="contact_lists")
    contact_list = models.JSONField(default=[])
    is_active = models.BooleanField(default=False)
    organisation_name = models.CharField(max_length=255,null=True)  # Assuming VARCHAR has a maximum length
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255)  # Assuming VARCHAR has a maximum length
    modified_by = models.CharField(max_length=255)  # Assuming VARCHAR has a maximum length
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'contact_list'  # Specify the table name if it's different
 
    def __str__(self):
        return self.campaign.campaign_name
    

class ScheduleCampaign(models.Model):
    schedule_note = models.TextField()
    campaign = models.ForeignKey("Campaign", on_delete=models.SET_NULL, null=True, related_name="schedule_campaign")
    schedule_date = models.DateTimeField()
    is_ongoing = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, default="SYSTEM")
    modified_by = models.CharField(max_length=255, default="SYSTEM")
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Schedule: {self.schedule_note} - Date: {self.schedule_date}"    