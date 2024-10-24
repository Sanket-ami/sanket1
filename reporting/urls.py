from django.urls import path,include
from . import views
urlpatterns = [
    path('report_download', views.report_download, name='report_download'),
]
