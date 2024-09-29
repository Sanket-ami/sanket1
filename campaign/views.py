from django.shortcuts import render,redirect
from django.contrib import messages
from django.http.response import HttpResponseRedirect,JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from zonoapp.models import User
from voice.models import Voice
from agent.models import Agent
from .models import Campaign
from django.contrib.auth import login,logout,authenticate
import json
from provider.models import Provider
from .models import Campaign
from django.core.paginator import Paginator



## render create campaign page
@login_required(login_url="/login_home")
def create_campaign(request):
    if request.method == "GET":

        telephony_providers_list =  Provider.objects.filter(provider_type="telephony")
        if request.user.is_superuser:
            org_names = User.objects.filter(is_deleted=False).values_list('organisation_name',flat=True)
        else:
            org_names = User.objects.filter(is_deleted=False,username=request.user).values_list('organisation_name',flat=True)

        print('org_names ',org_names)

        available_agents = Agent.objects.filter(is_deleted=False)

        if not request.user.is_superuser:
            available_agents = available_agents.filter(organisation_name__in=org_names)
        print('available_agents ',available_agents)
        # available_voice = Agent.objects.filter(is_deleted=False)

        context = {"breadcrumb":{"title":"Create Campaign","parent":"Pages", "child":"Sample Page"},
                   "telephony_providers_list":telephony_providers_list,"org_names":org_names,
                   "available_agents":available_agents
                   }   
        
        return render(request,'pages/campaign/create_campaign.html',context)
    elif request.method == "POST":
        data = json.loads(request.body)
        print("datad ",data)

        provider = Provider.objects.get(id=data['provider'])
        agent = Agent.objects.get(id=data['agent'])
        agent.agent_prompt = data['prompt']
        agent.save()

        campaign = Campaign.objects.create(
            campaign_name=data['campaign_name'],
            is_schedule=data['is_schedule'],
            organisation_name=data['organisation_name'],
            show_transcript=data['show_transcript'],
            process_type=data['process_type'],
            provider=provider,
            contact_list = data['contact_list'],
            agent=agent,
            show_recording=data['show_recording'],
            show_numbers=data['show_numbers'],
            created_by=request.user,  # or request.user if you have authentication
            modified_by=request.user
        )

        return JsonResponse({"message": "Campaign created successfully!", "campaign_id": campaign.id,"success":True})

    return JsonResponse({"error": "Invalid request method","success":False, "error":True }, status=500)
    
## render view campaign page
@login_required(login_url="/login_home")    
def campaign_list(request):
    search_query = request.GET.get('q', '')  # Get the search query from the URL
    campaigns = Campaign.objects.filter(campaign_name__icontains=search_query)  # Filter campaigns based on the search query
    
    paginator = Paginator(campaigns, 10)  # Show 10 campaigns per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'pages/campaign/list_campaign.html', context)


def edit_campaign():
    pass
def delete_campaign():
    pass