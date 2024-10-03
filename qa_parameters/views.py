from django.shortcuts import render
from .models import QAParameters
import json
from django.http import JsonResponse

# Create your views here.

def qa_parameters(request):
    if request.method == 'GET':
        qa_parameter = QAParameters.objects.all()
        return render(request, 'pages/qa_parameters/qa_parameters.html', {'qa_parameters': qa_parameter})
    elif request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        qa_parameter = QAParameters.objects.create(
            organisation_name = data['organisation_name'],
            parameters_name = data['parameter_name'],
            qa_parameters = data['qa_parameter']
        )
        print(qa_parameter.qa_parameters)
        return JsonResponse({'id': qa_parameter.id}, status=201) 
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        qa_parameter = QAParameters.objects.get(id=data['id'])
        qa_parameter.delete()
        try:
            return JsonResponse({'status': 'User deleted successfully', 'status_code': 200}, status=200)
        except QAParameters.DoesNotExist:
            return JsonResponse({'status': 'User not found', 'status_code': 404}, status=404)
        except Exception as e:
            return JsonResponse({'status': f'User deletion failed: {e}', 'status_code': 400}, status=400)
    

       

