from django.urls import path
from provider.views import provider_view, provider_delete, provider_form , edit_provider

urlpatterns = [
    path('provider/', provider_view, name='provider_view'),  # Provider table page
    path('provider/add/', provider_form, name='provider_form'),  # Provider form page
    path('provider/delete/', provider_delete, name='delete_provider'),  
    path('edit_provider/', edit_provider, name='edit_provider'),

]
