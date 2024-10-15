from django.http import HttpResponse
import csv
from campaign.models import Campaign, CallLogs  # Import your models
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url="/login_home")
def report_download(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Filter campaign IDs
        campaign_ids = Campaign.objects.filter(organisation_name='ami').values_list('id', flat=True)

        # Fetch data within the specified date range
        data = CallLogs.objects.filter(
            created_at__gt=start_date,
            created_at__lte=end_date,
            campaign_id__in=campaign_ids
        )
        print(len(data))
        # Prepare the CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="call_logs_report.csv"'

        writer = csv.writer(response)

        # Write CSV header
        headers = [
            "call_id",
            "created_at",
            "claim_id",
            "contact_id",
            "claim_amount",
            "claim_status",
            "patient_name",
            "contact_number",
            "submission_date",
            "insurance_provider",
            "call_status",
            "campaign_id",
            "start_time",
            "end_time",
            "call_duration"
        ]
        writer.writerow(headers)

        # Write data rows
        for call_log in data:
            # Fetching each field, defaulting to empty string if not present
            row = [
                call_log.call_id if hasattr(call_log, 'call_id') else "",
                call_log.created_at if hasattr(call_log, 'created_at') else "",
                call_log.claim_id if hasattr(call_log, 'claim_id') else "",
                call_log.contact_id if hasattr(call_log, 'contact_id') else "",
                call_log.claim_amount if hasattr(call_log, 'claim_amount') else "",
                call_log.claim_status if hasattr(call_log, 'claim_status') else "",
                call_log.patient_name if hasattr(call_log, 'patient_name') else "",
                call_log.contact_number if hasattr(call_log, 'contact_number') else "",
                call_log.submission_date if hasattr(call_log, 'submission_date') else "",
                call_log.insurance_provider if hasattr(call_log, 'insurance_provider') else "",
                call_log.call_status if hasattr(call_log, 'call_status') else "",
                call_log.campaign_id if hasattr(call_log, 'campaign_id') else "",
                call_log.start_time if hasattr(call_log, 'start_time') else "",
                call_log.end_time if hasattr(call_log, 'end_time') else "",
                call_log.call_duration if hasattr(call_log, 'call_duration') else ""
            ]
            writer.writerow(row)

        return response

    return render(request, 'pages/report/report.html', {"breadcrumb": {"title": "Report", "parent": "Pages", "child": "Download Report"}})
