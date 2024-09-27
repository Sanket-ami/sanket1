
from django.contrib import admin
from django.urls import path,include
from provider.views import provider_view, provider_delete

urlpatterns = [
    path('get_provider', provider_view, name='provider_view'),
    path('delete/<int:provider_id>/', provider_delete, name='delete_provider')
]
# delete/<int:provider_id>/