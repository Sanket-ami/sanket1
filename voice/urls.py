
from django.urls import path,include
from voice.views import voice_view, edit_voice
urlpatterns = [
    path('', voice_view, name='voice_view'),
    path('voice/edit/', edit_voice, name='edit_voice')
]