from django.urls import path
from .import views

urlpatterns = [
        path('/create_campaign', views.create_campaign, name='create_campaign'),
        path('/manage_campaign', views.campaign_list, name='manage_campaign'),
        path('/campaign/edit/<int:id>', views.edit_campaign, name='edit_campaign'),
        path('/campaign/delete/<int:id>', views.delete_campaign, name='delete_campaign'),  
        path('campaign/<int:campaign_id>/contacts/', views.contact_list, name='contact_list'),      
        path('campaign/<int:campaign_id>/contacts/delete', views.delete_contact, name='delete_contacts'),
        path('/start_campaign', views.start_campaign, name='start_campaign'),
        path('/call_logs', views.list_call_logs, name='list_call_logs'),
        path('/call_details', views.fetch_call_details, name='fetch_call_details'),
        path('/fetch_audio', views.fetch_audio, name='fetch_audio'),
        path('/edit_summary', views.edit_summary, name='edit_summary'),
        path('/edit_transcript', views.edit_transcript, name='edit_transcript'),
        
        
        
        
]