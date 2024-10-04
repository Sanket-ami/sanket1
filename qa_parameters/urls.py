
from django.urls import path,include
from .views import qa_parameters
urlpatterns = [
    path('', qa_parameters, name='qa_parameter'),
]