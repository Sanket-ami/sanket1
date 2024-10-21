from django.shortcuts import render,redirect,get_object_or_404
from provider.models import Provider
from django.http import JsonResponse
from django.core.paginator import Paginator
import json
from django.contrib.auth.decorators import login_required

@login_required(login_url="/login_home")
def provider_view(request):
    if request.method == 'GET':
        providers = Provider.objects.all().filter(is_delete=False).order_by('-id')
        providers = Provider.objects.all().filter(is_delete=False)
        paginator = Paginator(providers, 10) 
        page_number = request.GET.get('page')  
        providers = paginator.get_page(page_number)  
        return render(request, 'pages/provider/provider_table.html', {'providers': providers,"breadcrumb":{"title":"AI Configuration","parent":"Pages", "child":"Provider"}})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required(login_url="/login_home") 
def provider_form(request):
    if request.method == 'GET':
        return render(request, 'pages/provider/provider_form.html')  # Renders the form page

    elif request.method == 'POST':
        # Use request.POST to retrieve form data
        provider_name = request.POST.get('provider_name')
        provider_type = request.POST.get('provider_type')
        provider_config = request.POST.get('provider_config')

        # Check if any of the required fields are missing
        if not provider_name or not provider_type or not provider_config:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            Provider.objects.create(
                provider_name=provider_name,
                provider_type=provider_type,
                provider_config=provider_config
            )
            return JsonResponse({'status': 'created', 'status_code': 201}, status=201)
        except Exception as e:
            # Catch any exceptions and return a JSON error response
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required(login_url="/login_home")
def provider_delete(request):
    try:
        request_body = json.loads(request.body)
        provider_id = request_body['provider_id']  # Get the provider ID from the request body

        provider = get_object_or_404(Provider, id=provider_id)  # Use get_object_or_404 for better error handling
        provider.is_delete = True  # Mark the provider as deleted
        provider.save()
        return JsonResponse({"success": True, "message": "Provider deleted successfully!"})
    except Exception as e:
        print(e)  # Print the error for debugging
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Provider  # Import your Provider model

def edit_provider(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        provider_id = data.get('provider_id')
        provider_name = data.get('provider_name')
        provider_type = data.get('provider_type')
        provider_config = data.get('provider_config')

        # Fetch the Provider object to update
        provider = get_object_or_404(Provider, id=provider_id)
        provider.provider_name = provider_name  # Update name
        provider.provider_type = provider_type  # Update type
        provider.provider_config = provider_config  # Update configuration
        provider.save()  # Save the changes
        provider_types = Provider.objects.values_list('provider_type', flat=True).distinct()

        return JsonResponse({'status': 'success', 'provider_id': provider.id,'provider_types':provider_types})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    