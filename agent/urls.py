from django.urls import path
from .import views

urlpatterns = [
        path('agent', views.agent_create, name='agent_create'),
]