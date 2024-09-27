from django.shortcuts import render,redirect
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate

from provider.models import Provider
 




## render create campaign page
@login_required(login_url="/login_home")
def create_campaign(request):
    if request.method == "GET":

        telephony_providers_list =  Provider.objects.filter(provider_type="telephony")

        print('telephony_providers_list ',telephony_providers_list)
        context = {"breadcrumb":{"title":"Create Campaign","parent":"Pages", "child":"Sample Page"},"telephony_providers_list":telephony_providers_list}   
        
        return render(request,'pages/campaign/create_campaign.html',context)
    elif request.method == "POST":
        pass
    
    