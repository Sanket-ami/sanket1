from django.db import models
from campaign.models import Campaign

# Create your models here.
class QAParameters(models.Model):
    # Assuming the foreign key is pointing to a Campaign model
    parameters_name = models.CharField(max_length=255)
    qa_parameters = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255)  # Assuming VARCHAR has a maximum length
    modified_by = models.CharField(max_length=255)  # Assuming VARCHAR has a maximum length
    is_deleted = models.BooleanField(default=False)
    organisation_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'qa_parameters'  # Specify the table name if it's different
 

    def __str__(self):
        return self.call_logs  # or any other field you prefer to display