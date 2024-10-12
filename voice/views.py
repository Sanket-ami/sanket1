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
                voice_config = voice.voice_configuration
            except json.JSONDecodeError:
                voice_config = {}  
            voices_list.append({
                'voice_name': voice.voice_name,
                'voice_provider': voice.voice_provider,
                'voice_configuration': voice_config
            })
        org_names = User.objects.all().distinct('organisation_name')
        voice_provider = Provider.objects.all()
        paginator = Paginator(voices, 9)
        page_number = request.GET.get('page')
        voices_list = paginator.get_page(page_number)
        return render(request, 'pages/voice/voice.html', {'page_obj': voices_list, 'voices': voices_list, 'org_names': org_names, 'providers_list': voice_provider,"breadcrumb":{"title":"Voice","parent":"Pages", "child":"Voice"}})

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
            print(voice_provider)
            #download the sample files
            # import pdb; pdb.set_trace()
            if voice_provider.provider_name == 'ElevenLabs':
                get_voice(voice.voice_id)
            elif voice_provider.provider_name == "Cartesia":
                print(voice.voice_id)
                get_voice_cartesia(voice, "/home/sanket.chavan/Documents/revamp/callbotics_revamp/voice/cartesia_voice_list.json")
                print(voice.voice_id)

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

import requests
import os

def get_voice(voice_id):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}"
        headers = {"xi-api-key": "sk_037c3e6c88a4306c8916be76f2b44783bc8d77d282d68388"}
        response = requests.get(url,headers=headers)
        response.raise_for_status()  
        voice_data = response.json()
        
        preview_url = voice_data.get("preview_url")
        save_dir = "zonoapp/static/assets/audio"

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        if preview_url:
            audio_response = requests.get(preview_url)
            audio_response.raise_for_status()  # Raise an error for bad responses

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

import json
import os
import requests
def get_voice_cartesia(voice, json_file):
    try:
        # Load the JSON data from the file
        with open(json_file, 'r') as file:
            voices_data = json.load(file)
        print("JSON data loaded successfully.")
        
        # Search for the voice entry with the matching voice_id
        matching_voice = None
        for voice_data in voices_data:
            if voice.voice_id == voice_data.get("id"):
                matching_voice = voice_data
                break
        
        if matching_voice:
            # Extract the sample URL and save location
            sample_url = matching_voice.get("sample")
            print(f"Sample URL found: {sample_url}")
            
            save_dir = "zonoapp/static/assets/audio"
            os.makedirs(save_dir, exist_ok=True)  # Create the directory if it doesn't exist
            
            if sample_url:
                # Fetch the audio file from the URL
                print(f"Attempting to download the file from {sample_url}")
                response = requests.get(sample_url, stream=True)
                
                # Debug: Check response status
                print(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    # Use voice_name from the Voice model instance
                    voice_name = voice.voice_name.replace(" ", "_")  # Clean the name
                    file_name = os.path.join(save_dir, f"{voice_name}.wav")  # Store using voice_name
                    print(f"Saving audio to: {file_name}")
                    
                    # Write the audio content to a file
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
        print(f"JSON file {json_file} not found. Please check the file path.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the audio file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
