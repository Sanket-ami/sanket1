from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.shortcuts import render
import json
from .models import Voice
from provider.models import Provider 
from zonoapp.models import User
from provider.models import Provider
from django.core.paginator import Paginator


def voice_view(request):
    if request.method == 'GET':
        voices_list = []
        voices = Voice.objects.all()
        for voice in voices:
            try:
                voice_config = json.loads(voice.voice_configuration)
                print(voice_config)
            except json.JSONDecodeError:
                voice_config = {}  # 
            voices_list.append({
                'voice_name': voice.voice_name,
                'voice_provider': voice.voice_provider,
                'voice_configuration': voice_config
            })
        org_names = User.objects.all()
        voice_provider = Provider.objects.all()
        paginator = Paginator(voices, 10)
        page_number = request.GET.get('page')
        voices_list = paginator.get_page(page_number)
        return render(request, 'pages/voice/voice.html', {'page_obj': voices_list, 'voices': voices_list, 'org_names': org_names, 'providers_list': voice_provider})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            voice_provider = Provider.objects.get(id=data['voice_provider'])
            voice = Voice.objects.create(
                voice_id=data['voice_id'],
                voice_provider=voice_provider,  # Use voice_provider_id to link by ID
                oragnisation_name=data['organisation_name'],
                voice_configuration=data['voice_config'],
                voice_name=data.get('voice_name')
            )
            return JsonResponse({'id': voice.id}, status=201)

        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        
    elif request.method == 'PUT':
           
        try:
            data = json.loads(request.body)
            try:
                voice = Voice.objects.get(id=id)
            except Voice.DoesNotExist:
                return JsonResponse({"error": "Voice record not found"}, status=404)
            voice.oragnisation_name = data.get('organization_name', voice.oragnisation_name)
            voice.voice_configuration = data.get('voice_configuration', voice.voice_configuration)
            voice.modified_by = data.get('modified_by', voice.modified_by)
            voice.save()
            return JsonResponse(voice, status=200)
        except Exception:
            pass

    return JsonResponse({'error': 'Method not allowed'}, status=405)
