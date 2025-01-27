from django.shortcuts import render
from .models import QAParameters
import json
from django.http import JsonResponse
from zonoapp.models import User
# Create your views here.
from django.contrib.auth.decorators import login_required


@login_required(login_url="/login_home")
def qa_parameters(request):
    if request.method == 'GET':
        qa_parameter = QAParameters.objects.all().filter(is_deleted=False)
        if request.user.is_superuser:
            org_names = User.objects.filter(is_deleted=False).values_list('organisation_name',flat=True).distinct()
        else:
            org_names = User.objects.filter(is_deleted=False,username=request.user).values_list('organisation_name',flat=True)
        return render(request, 'pages/qa_parameters/qa_parameters.html', {'qa_parameters': qa_parameter, 'org_names': org_names,"breadcrumb":{"title":"QA Parameter","parent":"Pages", "child":"QA Parameter"}})
    elif request.method == 'POST':
        data = json.loads(request.body)
        qa_parameter = QAParameters.objects.create(
            organisation_name = data['organisation_name'],
            parameters_name = data['parameter_name'],
            qa_parameters = data['qa_parameter']
        )
        return JsonResponse({'id': qa_parameter.id}, status=201) 
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        qa_parameter = QAParameters.objects.get(id=data['id'])
        qa_parameter.is_deleted = True
        qa_parameter.save()
        try:
            return JsonResponse({'status': 'User deleted successfully', 'status_code': 200}, status=200)
        except QAParameters.DoesNotExist:
            return JsonResponse({'status': 'User not found', 'status_code': 404}, status=404)
        except Exception as e:
            return JsonResponse({'status': f'User deletion failed: {e}', 'status_code': 400}, status=400)
    

       

