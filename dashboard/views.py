from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta, time
from campaign.models import CallLogs, Campaign, Transcript
from zonoapp.models import User
from django.contrib.auth.decorators import login_required
import json

def update_interval_count(intervals, durations):
    for duration in durations:
        if duration < 5:
            intervals['< 5'] += 1
        elif 5 <= duration < 10:
            intervals['5-10'] += 1
        elif 10 <= duration < 20:
            intervals['10-20'] += 1
        elif 20 <= duration < 30:
            intervals['20-30'] += 1
        elif 30 <= duration < 40:
            intervals['30-40'] += 1
        elif 40 <= duration < 50:
            intervals['40-50'] += 1
        else:  # duration >= 50
            intervals['> 50'] += 1
    return intervals

def qa_analysis(request):
    last_10_call = Transcript.objects.all().filter(organisation_name=request.user.organisation_name).exclude(transcript__isnull=True, qa_analysis__isnull=True).order_by('-id')[:10]
    met = []
    not_met = []
    for call in last_10_call:
        if type(call.qa_analysis) == str:
            try:
                qa_analysis = call.qa_analysis.replace("```json", "").replace("```", "").replace("\n", "")
                qa_analysis = json.loads(qa_analysis)
                met_count = [i for i in qa_analysis if i['result']=='met']
                met.append(len(met_count))
                not_met.append(len(qa_analysis)-len(met_count))
            except Exception:
                pass
        else:
            
            met_count = [i for i in call.qa_analysis if i['result']=='met']
            met.append(len(met_count))
            not_met.append(len(call.qa_analysis)-len(met_count))

    return met, not_met
    

@login_required(login_url="/login_home")
def calls_per_hour(request):
    
    if request.user.is_superuser:
        organisation_list = User.objects.values('organisation_name').distinct('organisation_name')
    else:
        organisation_list = [{'organisation_name': request.user.organisation_name}]
    
    if request.GET.get('organisation'):
        organisation = request.GET.get('organisation')
        return render(request, 'pages/dashboard/dashboard.html', {"breadcrumb":{"title":"Dashboard","parent":"Pages", "child":"Calls"}, 'organisation_list': organisation_list, 'organisation': organisation})     


    if request.method == 'GET':
        event = request.GET.get('event')
        if event:
            org = request.GET.get('org')
            campaign_ids = Campaign.objects.filter(organisation_name=org).values_list('id', flat=True)
            today = datetime.today() + timedelta(hours=5, minutes=30)
            total_dur_list = []
            failedCalls = 0
            avg_handling_time = []
            dates = []
            number_of_calls = {'< 5': 0, '5-10': 0, '10-20': 0, '20-30': 0, '30-40': 0, '40-50': 0, '> 50':0}
            event_date_range = {'daily': 1, 'weekly': 7, 'monthly': 30}
            date_range = event_date_range[request.GET.get('event')]
            connected_call = 0
            total_calls = []
            daily_failed_call = 0
            failed_calls = []
            for date in range(date_range):  # Assuming 'monthly' as the default event type
                start_time = datetime.combine(today.date() - timedelta(days=date), time.min)
                end_time = datetime.combine(today.date()-timedelta(days=date+1), time.min)
                data = CallLogs.objects.filter(created_at__lte=start_time, created_at__gte=end_time, campaign_id__in=campaign_ids)
                total_dur = 0
                total_call = data.count() 
                total_calls.append(data.count())
                results = []
                for call in data:
                    results.append({'created_at': call.created_at})
                    if call.call_status not in ['ongoing', 'completed']:
                        continue
                    if hasattr(call, 'call_duration'):
                        connected_call += 1
                        if int(call.call_duration) < 10:
                            failedCalls += 1
                            daily_failed_call += 1
                            pass
                        total_dur += int(call.call_duration)
                        total_dur_list.append(int(int(call.call_duration) / 60))
                failed_calls.append(daily_failed_call)
                daily_failed_call = 0
                dates.append(end_time.strftime("%d"))
                avg_handling_time.append(int(total_dur / 60) / connected_call if connected_call > 0 else 0)

            interval = update_interval_count(number_of_calls, total_dur_list)
            number_of_calls, number_of_calls_labels = list(interval.values()), list(interval.keys())

            if request.user.is_superuser:
                organisation_list = User.objects.values('organisation_name').distinct('organisation_name')
            else:
                organisation_list = [{'organisation_name': request.user.organisation_name}]
            met, not_met = qa_analysis(request)
            response_data ={
                'results': results,
                'avg_handling_time': avg_handling_time,
                'connected_call': connected_call,
                'not_connected_call': total_call - connected_call,
                'dates': dates,
                'number_of_calls': number_of_calls,
                'total_calls': total_calls,
                'number_of_calls_labels': number_of_calls_labels,
                'call_overview':dates,
                'failed_calls': failed_calls,
                'totalDialedCalls': connected_call,
                'compromised_call':connected_call - failedCalls,
                'failed_call': failedCalls, 
                'met': met,
                'not_met': not_met,
                'total_qa_calls': [f'Call {count}' for count in range(1, len(met)+1)],
                'met_percent': (
        0 if (sum(met) + sum(not_met)) == 0 
        else round(sum(met) * 100 / (sum(met) + sum(not_met)))
                ),
                'met_sum': sum(met),
                'not_met_sum': sum(not_met)
            }
            return JsonResponse(response_data)  
        return render(request, 'pages/dashboard/dashboard.html', {"breadcrumb":{"title":"Dashboard","parent":"Pages", "child":"Dashboard"}, 'organisation_list': organisation_list})
    return render(request, 'pages/dashboard/dashboard.html', {"breadcrumb":{"title":"Dashboard","parent":"Pages", "child":"Dashboard"}, 'organisation_list': organisation_list})     
