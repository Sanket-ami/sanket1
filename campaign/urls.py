from django.urls import path
from .import views

urlpatterns = [
        path('/create_campaign', views.create_campaign, name='create_campaign'),
]