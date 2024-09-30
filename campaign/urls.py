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
        
]