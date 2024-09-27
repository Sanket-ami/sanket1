
from django.contrib import admin
from django.urls import path,include
from provider.views import provider_view

urlpatterns = [
    path('get_provider', provider_view, name='provider_view'),
]
