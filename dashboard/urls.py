
from django.urls import path,include
from .views import calls_per_hour
urlpatterns = [
    path('', calls_per_hour, name='calls_per_hour'),
]