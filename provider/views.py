from django.shortcuts import render
from provider.models import Provider
from django.http import JsonResponse
import json

def provider_view(request):
    if request.method == 'GET':
        providers = Provider.objects.all()
        provider_list = [
            {
                'id': provider.id,
                'provider_name': provider.provider_name,
                'provider_config': provider.provider_config,
                'is_delete': provider.is_delete
            }
            for provider in providers
        ]
        return render(request, 'pages/provider/provider.html', {'providers': provider_list})

    elif request.method == 'POST':
        try:
            provider = Provider.objects.create(
                provider_name=request.POST.get('provider_name'),
                  provider_config=request.POST.get('provider_config'),
              
            )
            return JsonResponse({'status': 'created', 'status_code':201}, status=201)

        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)