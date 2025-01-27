from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.http.response import HttpResponseRedirect,JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from zonoapp.models import User
from django.contrib.auth import login,logout,authenticate
from .models import Agent
from provider.models import Provider
from django.core.paginator import Paginator
from voice.models import Voice
import json

## render create campaign page
@login_required(login_url="/login_home")
def agent_create(request):
    if request.method == "GET":
        telephony_providers_list =  Provider.objects.filter(provider_type="telephony")
        llm_providers_list =  Provider.objects.filter(provider_type="llm")
        if request.user.is_superuser:
            org_names = User.objects.filter(is_deleted=False).values_list('organisation_name',flat=True).distinct()
        else:
            org_names = User.objects.filter(is_deleted=False,username=request.user).values_list('organisation_name',flat=True).distinct()
            if request.user.role.role == 'Caller' or request.user.role.role == 'QA':
                return render(request,'pages/error-pages/error-403.html')
            
        # voices list
        voices = Voice.objects.filter(is_delete=False)
        print(voices)

        print('org_names ',org_names)
        search_query = request.GET.get('search', '')
        agents = Agent.objects.filter( is_deleted=False, organisation_name__in=org_names).order_by('-modified_at')
        if search_query:
            agents = agents.filter(agent_name__icontains=search_query)

        # Pagination: show 10 agents per page
        paginator = Paginator(agents, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {"breadcrumb":{"title":"Agent","parent":"Pages", "child":"Agent Management "},"llm_providers_list":llm_providers_list,"org_names":org_names,'page_obj': page_obj, 'search_query': search_query,'voices':voices,"telephony_providers_list":telephony_providers_list}   
        
        return render(request,'pages/agent/agent_list.html',context)
    elif request.method == "POST":
        try:
            print("request recieved!!!!!!!")
            # Parse the incoming JSON data
            data = json.loads(request.body)
            print('agent_data ',data)
            # Extract the form fields
            agent_name = data.get('agent_name')
            organisation_name = data.get('organisation_name')
            agent_provider_name = data.get('agent_provider')
            voice_id = data.get('voice')
            agent_configuration = data.get('agent_configuration')
            agent_telephony_id = data.get('agent_telephony')

            if Agent.objects.filter(agent_name=agent_name, organisation_name=organisation_name).exists():
                return JsonResponse({"message": "Agent with this name in organisation already exists!", "success": False})
            # Validate the form fields
            if not agent_name or not organisation_name or not agent_provider_name or not voice_id or not agent_configuration:
                return JsonResponse({"success": False, "error": "All fields are required."}, status=400)

            # Parse agent_configuration JSON
            try:
                agent_config_json = json.loads(agent_configuration)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Invalid JSON in agent configuration."}, status=400)

            # Get the related provider and voice
            agent_provider = get_object_or_404(Provider, provider_name=agent_provider_name)
            agent_telephony = get_object_or_404(Provider,id = agent_telephony_id)
            voice = get_object_or_404(Voice, id=voice_id)

            # Create a new Agent object
            Agent.objects.create(
                agent_name=agent_name,
                organisation_name=organisation_name,
                agent_provider=agent_provider,
                agent_telephony = agent_telephony,
                voice=voice,
                agent_configuration=agent_config_json,
                created_by="system",  # Assuming system is creating it, modify as needed
                modified_by="system"
            )
            
            # Success response
            return JsonResponse({"success": True,"message":"Agent added Successfully!","status_code":200})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e),"status_code":500}, status=500)        

    elif request.method == "PUT" :
        try:
            data = json.loads(request.body)
            agent_id = data.get('agent_id')
            agent_name = data.get('agent_name')
            organisation_name = data.get('organisation_name')
            agent_provider_name = data.get('agent_provider')
            voice_id = data.get('voice')
            agent_configuration = data.get('agent_configuration')
            agent_telephony_name = data.get('agent_telephony')
            if not agent_id or not agent_name or not organisation_name or not agent_provider_name or not voice_id or not agent_configuration or not agent_telephony_name:
                return JsonResponse({"success": False, "error": "All fields are required."}, status=400)

            agent = get_object_or_404(Agent, id=agent_id)
            agent.agent_name = agent_name
            agent.organisation_name = organisation_name
            agent.agent_provider = get_object_or_404(Provider, provider_name=agent_provider_name)
            agent.voice = get_object_or_404(Voice, id=voice_id)
            agent.agent_telephony = get_object_or_404(Provider,provider_name=agent_telephony_name)
            try:
                agent.agent_configuration = json.loads(agent_configuration)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Invalid JSON in agent configuration."}, status=400)

            agent.save()

            return JsonResponse({"success": True, "message": "Agent updated successfully!"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


############ delete agent #############
def agent_delete(request):
    try:
        request_body = json.loads(request.body)
        agent_id = request_body['agent_id']

        agent = get_object_or_404(Agent, id=agent_id)
        agent.is_deleted = True
        agent.save()
        return JsonResponse({"success": True, "message": "Agent deleted successfully!"})
    except Exception as e:
        print(e)
        return JsonResponse({"success": False, "error": str(e)}, status=500)