import json
import os
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.shortcuts import render
from .models import Voice
from provider.models import Provider
from zonoapp.models import User
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404


@login_required(login_url="/login_home")
def voice_view(request):
    if request.method == 'GET':
        voices_list = []
        search_query = request.GET.get('search', '')
        voices = Voice.objects.all()
        if search_query:
            voices = voices.filter(voice_name__icontains=search_query)
        for voice in voices:
            try:
                voice_config = voice.voice_configuration
            except json.JSONDecodeError:
                voice_config = {}  
            voices_list.append({
                'voice_name': voice.voice_name,
                'voice_provider': voice.voice_provider,
                'voice_configuration': voice_config,
                'id': voice.id  # Include the voice ID for editing
            })
        org_names = User.objects.all().distinct('organisation_name')
        voice_provider = Provider.objects.all()
        paginator = Paginator(voices, 9)
        page_number = request.GET.get('page')
        voices_list = paginator.get_page(page_number)
        return render(request, 'pages/voice/voice.html', {
            'page_obj': voices_list,
            'voices': voices_list,
            'org_names': org_names,
            'providers_list': voice_provider,
            "breadcrumb": {"title": "Voice", "parent": "Pages", "child": "Voice"}
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            voice_provider = Provider.objects.get(id=data['voice_provider'])
            if Voice.objects.filter(voice_name=data['voice_name'], organisation_name=data['organisation_name']).exists():
                return JsonResponse({"message": "Voice with this name in organisation already exists!", "success": False})
            voice = Voice.objects.create(
                voice_id=data['voice_id'],
                voice_provider=voice_provider,
                oragnisation_name=data['organisation_name'],
                voice_configuration=data['voice_config'],
                voice_name=data.get('voice_name')
            )

            # Download the sample files
            if voice_provider.provider_name == 'ElevenLabs':
                get_voice(voice.voice_id)
            elif voice_provider.provider_name == "Cartesia":
                get_voice_cartesia(voice, "/home/sanket.chavan/Documents/revamp/callbotics_revamp/voice/cartesia_voice_list.json")

            return JsonResponse({'id': voice.id}, status=201)

        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            voice_id = data.get('id')
            voice = Voice.objects.get(id=voice_id)
            voice.voice_configuration = data.get('voice_config', voice.voice_configuration)
            voice.save()
            return JsonResponse({'success': True}, status=200)
        except Voice.DoesNotExist:
            return JsonResponse({"error": "Voice record not found"}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_voice(voice_id):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}"
        headers = {"xi-api-key": "sk_037c3e6c88a4306c8916be76f2b44783bc8d77d282d68388"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        voice_data = response.json()
        
        preview_url = voice_data.get("preview_url")
        save_dir = "zonoapp/static/assets/audio"

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        if preview_url:
            audio_response = requests.get(preview_url)
            audio_response.raise_for_status()

            file_name = os.path.join(save_dir, f"{voice_id}.mp3")

            with open(file_name, 'wb') as audio_file:
                audio_file.write(audio_response.content)
            print(f"Audio file saved to {file_name}")
        else:
            print("No preview URL found.")
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def get_voice_cartesia(voice, json_file):
    try:
        with open(json_file, 'r') as file:
            voices_data = json.load(file)
        
        matching_voice = next((v for v in voices_data if v.get("id") == voice.voice_id), None)

        if matching_voice:
            sample_url = matching_voice.get("sample")
            save_dir = "zonoapp/static/assets/audio"
            os.makedirs(save_dir, exist_ok=True)

            if sample_url:
                response = requests.get(sample_url, stream=True)

                if response.status_code == 200:
                    voice_name = voice.voice_name.replace(" ", "_")
                    file_name = os.path.join(save_dir, f"{voice_name}.wav")

                    with open(file_name, 'wb') as audio_file:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                audio_file.write(chunk)
                    
                    print(f"Audio file saved successfully to {file_name}")
                else:
                    print(f"Failed to download audio. Status code: {response.status_code}")
            else:
                print("No sample URL found for the matching voice.")
        else:
            print(f"No matching voice found for ID: {voice.voice_id}")

    except FileNotFoundError:
        print(f"JSON file {json_file} not found.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the audio file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def edit_voice(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        voice_id = data.get('voice_id')
        voice_config = data.get('voice_config')

        # Fetch the Voice object to update
        voice = get_object_or_404(Voice, id=voice_id)
        voice.voice_configuration = voice_config  # Update the configuration
        voice.save()  # Save the changes

        return JsonResponse({'status': 'success', 'voice_id': voice.id})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def delete_voice(request, voice_id):
    try:
        voice = get_object_or_404(Voice, id=voice_id)
        voice.is_delete=True
        voice.save()
        return JsonResponse({'message': 'Voice deleted successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
