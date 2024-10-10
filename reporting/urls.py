from django.urls import path,include
from .views import report
urlpatterns = [
    path('report_download', views.report, name='report_download'),
]
