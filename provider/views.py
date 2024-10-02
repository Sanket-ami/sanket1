from django.shortcuts import render
from provider.models import Provider
from django.http import JsonResponse
from django.core.paginator import Paginator
import json


def provider_view(request):
    if request.method == 'GET':
        providers = Provider.objects.all().filter(is_delete=False).order_by('-id')
        providers = Provider.objects.all().filter(is_delete=False)
        paginator = Paginator(providers, 10) 
        page_number = request.GET.get('page')  
        providers = paginator.get_page(page_number)  
        return render(request, 'pages/provider/provider_form.html', {'providers': providers})

    elif request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        try:
            Provider.objects.create(
                provider_name=data.get('provider_name'),  # provider_name
                provider_type=data.get('provider_type'),
                provider_config=data.get('provider_config')
            )
            return JsonResponse({'status': 'created', 'status_code':201}, status=201)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def provider_delete(request, provider_id: int):
    provider = Provider.objects.get(id=provider_id)
    provider.is_delete = True  
    provider.save()
    return JsonResponse({'success': True}, status=204)