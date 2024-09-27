
from django.contrib import admin
from django.urls import path,include
from voice.views import voice_view
urlpatterns = [
    path('', voice_view, name='voice_view'),
]
