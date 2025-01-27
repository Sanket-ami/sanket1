"""zono URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('zonoapp.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('provider/', include('provider.urls')),
    path('voice', include('voice.urls')),
    path('content',include('campaign.urls')),
    path('agent/',include('agent.urls')),
    path('qa_parameters', include('qa_parameters.urls')),
    path('reporting/', include('reporting.urls')),
]
