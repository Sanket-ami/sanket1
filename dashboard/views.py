from django.shortcuts import render
from campaign.models import CallLogs
import json
from datetime import datetime, timedelta

def calls_per_hour(request):
    if request.method == 'POST':
        print("post method")

    if request.GET.get('start_date'):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        results = []
        data = CallLogs.objects(created_at__gte=start_date, created_at__lt=end_date)
        print(data)
        for i in data:
            results.append({'created_at': i.created_at})
        print(start_date, end_date)
        print(results)

        return render(request,'pages/dashboard/dashboard.html', {'results': results, 'start_date': start_date, 'end_date': end_date})
        #return render(request, 'pages/qa_parameters/qa_parameters.html', {'qa_parameters': qa_parameter, 'org_names': org_names})

