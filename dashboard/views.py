from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta, time
from campaign.models import CallLogs

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


def calls_per_hour(request):
    if request.method == 'GET':
        event = request.GET.get('event')

        if event:
            today = datetime.today()
            total_dur_list = []
            connected_call_list = []
            total_call_list = []
            avg_handling_time = []
            dates = []
            number_of_calls = {'< 5': 0, '5-10': 0, '10-20': 0, '20-30': 0, '30-40': 0, '40-50': 0, '> 50':0}
            if event == 'daily':
               for date in range(1):  # Assuming 'monthly' as the default event type
                    start_time = datetime.combine(today.date() - timedelta(days=date), time.min)
                    end_time = datetime.combine(today.date()-timedelta(days=date+1), time.min)
                    print(start_time, end_time)

                    data = CallLogs.objects.filter(created_at__lt=start_time, created_at__gte=end_time)
                    total_dur = 0
                    connected_call = 0
                    total_call = data.count() 
                    results = []
                    for call in data:
                        results.append({'created_at': call.created_at})
                        if call.call_status not in ['ongoing', 'completed']:
                            continue
                        
                        if hasattr(call, 'call_duration'):
                            total_dur += call.call_duration
                            connected_call += 1
                            total_dur_list.appenf(call.call_duration)
                    dates.append(end_time.strftime("%d"))
                    avg_handling_time.append(total_dur / connected_call if connected_call > 0 else 0)
            elif event == 'weekly':
                for date in range(7):  # Assuming 'monthly' as the default event type
                    start_time = datetime.combine(today.date() - timedelta(days=date), time.min)
                    end_time = datetime.combine(today.date()-timedelta(days=date+1), time.min)
                    print(start_time, end_time)

                    data = CallLogs.objects.filter(created_at__lt=start_time, created_at__gte=end_time)
                    total_dur = 0
                    connected_call = 0
                    total_call = data.count() 
                    results = []
                    for call in data:
                        results.append({'created_at': call.created_at})
                        if call.call_status not in ['ongoing', 'completed']:
                            continue
                        
                        if hasattr(call, 'call_duration'):
                            total_dur += call.call_duration
                            connected_call += 1
                            total_dur_list.append(call.call_duration)

                    dates.append(end_time.strftime("%d"))
                    avg_handling_time.append(total_dur / connected_call if connected_call > 0 else 0)

            else:
                for date in range(30):  # Assuming 'monthly' as the default event type
                    start_time = datetime.combine(today.date() - timedelta(days=date), time.min)
                    end_time = datetime.combine(today.date()-timedelta(days=date+1), time.min)
                    print(start_time, end_time)

                    data = CallLogs.objects.filter(created_at__lt=start_time, created_at__gte=end_time)
                    total_dur = 0
                    connected_call = 0
                    total_call = data.count() 
                    results = []
                    for call in data:
                        results.append({'created_at': call.created_at})
                        if call.call_status not in ['ongoing', 'completed']:
                            continue
                        
                        if hasattr(call, 'call_duration'):
                            total_dur += call.call_duration
                            connected_call += 1
                            total_dur_list.append(call.call_duration)

                    dates.append(end_time.strftime("%d"))
                    avg_handling_time.append(total_dur / connected_call if connected_call > 0 else 0)

            interval = update_interval_count(number_of_calls, total_dur_list)
            number_of_calls, number_of_calls_labels = list(interval.values()), list(interval.keys())   #total_calls, failed_calls, call_overview
            response_data ={
                'results': results,
                'start_date': start_time,
                'end_date': end_time,
                'avg_handling_time': avg_handling_time,
                'total_call': total_call,
                'connected_call': connected_call,
                'not_connected_call': total_call - connected_call,
                'dates': dates,
                'number_of_calls': number_of_calls,
                'total_calls': [1, 2, 3, 4,5, 6, 7],
                'number_of_calls_labels': number_of_calls_labels,
                'call_overview':['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'failed_calls': [7, 2, 6, 4,5, 6, 7],
                'failed_call': 10,
                "compromised_call": 30,
                'totalDialedCalls': 1000,
                'compromisedCalls':330,
                'failedCalls': 670
            }

            return JsonResponse(response_data)  

        return render(request, 'pages/dashboard/dashboard.html')

    return render(request, 'pages/dashboard/dashboard.html', status=400)  # Optionally, render with an error status    implement this in function for daiky and weekly and monthly data


