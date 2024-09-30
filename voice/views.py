from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import json
from .models import Voice


def voice_view(request):
    if request.method == 'GET':
        voices = Voice.objects.all()
        voice_list = [
            {
                'id': voice.id,
                'voice_id': voice.voice_id,
                'voice_provider': voice.voice_provider.id if voice.voice_provider else None,
                'organisation_name': voice.oragnisation_name,
                'voice_configuration': voice.voice_configuration,
                'created_at': voice.create_at,
                'modified_at': voice.modified_at,
                'is_delete': voice.is_delete
            }
            for voice in voices
        ]
        return JsonResponse(voice_list, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            voice = Voice.objects.create(
                voice_id=data['voice_id'],
                voice_provider_id=data.get('voice_provider'),  # Use voice_provider_id to link by ID
                oragnisation_name=data['organisation_name'],
                voice_configuration=data['voice_configuration']
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
