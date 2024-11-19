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
        path('/start_campaign_secheduler', views.start_campaign_secheduler, name='start_campaign_secheduler'),
        path('/call_logs', views.list_call_logs, name='list_call_logs'),
        path('/call_details', views.fetch_call_details, name='fetch_call_details'),
        path('/fetch_audio', views.fetch_audio, name='fetch_audio'),
        path('/edit_summary', views.edit_summary, name='edit_summary'),
        path('/edit_qa', views.editQa, name='edit_qa'),
        path('/edit_transcript', views.edit_transcript, name='edit_transcript'),
        path('/live_call_list', views.live_call_list, name='live_call_list'),
        path('/live_transcript', views.live_transcript, name='live_transcript'),
        path('/end_call', views.end_call, name='end_call'),
        path('upload_contact_list/<int:campaign_id>/', views.upload_contact_list, name='upload_contact_list'),
        path('schedule_campaign/', views.schedule_campaign, name='schedule_campaign'),
        path('/sample_csv', views.sample_csv, name='sample_csv'),
        path('update_campaign/', views.update_campaign, name='update_campaign'),
        path('api/upload-csv/', views.upload_csv, name='upload_csv'),
        path('/get_prompt', views.get_prompt,name="get_campaign_prompt"),
        path('/edit_campaign_prompt', views.edit_prompt, name='edit_campaign_prompt'),  
        path('/delete/campaign/<int:campaign_id>', views.delete_campaign, name='delete_campaign')


]