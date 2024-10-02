from django.shortcuts import render,redirect
from django.contrib import messages
from django.http.response import HttpResponseRedirect,JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from zonoapp.models import User
from voice.models import Voice
from agent.models import Agent
from .models import Campaign, Transcript,QAParameters,CallLogs
from django.contrib.auth import login,logout,authenticate
import json
from provider.models import Provider
from .models import Campaign
from django.core.paginator import Paginator
import uuid
import threading
from django.shortcuts import get_object_or_404
from django.conf import settings
import requests
import time
from datetime import datetime
import os
from requests.auth import HTTPBasicAuth
from django.http import FileResponse
import io
from django.urls import reverse

## render create campaign page
@login_required(login_url="/login_home")
def create_campaign(request):
    if request.method == "GET":

        telephony_providers_list =  Provider.objects.filter(provider_type="telephony")
        if request.user.is_superuser:
            org_names = User.objects.filter(is_deleted=False).values_list('organisation_name',flat=True)
        else:
            org_names = User.objects.filter(is_deleted=False,username=request.user).values_list('organisation_name',flat=True)

        print('org_names ',org_names)

        available_agents = Agent.objects.filter(is_deleted=False)

        if not request.user.is_superuser:
            available_agents = available_agents.filter(organisation_name__in=org_names)
        print('available_agents ',available_agents)
        # available_voice = Agent.objects.filter(is_deleted=False)

        context = {"breadcrumb":{"title":"Create Campaign","parent":"Pages", "child":"Sample Page"},
                   "telephony_providers_list":telephony_providers_list,"org_names":org_names,
                   "available_agents":available_agents
                   }   
        
        return render(request,'pages/campaign/create_campaign.html',context)
    elif request.method == "POST":
        data = json.loads(request.body)
        print("datad ",data)

        provider = Provider.objects.get(id=data['provider'])
        agent = Agent.objects.get(id=data['agent'])
        agent.agent_prompt = data['prompt']
        agent.save()

        new_contact_list = []
        for contact in data['contact_list']:
            # add a unique identifiier to each contact
            contact["contact_id"] = "contact_"+str(uuid.uuid4().hex)
            new_contact_list.append(contact)

        campaign = Campaign.objects.create(
            campaign_name=data['campaign_name'],
            is_schedule=data['is_schedule'],
            organisation_name=data['organisation_name'],
            show_transcript=data['show_transcript'],
            process_type=data['process_type'],
            provider=provider,
            contact_list = new_contact_list,
            agent=agent,
            show_recording=data['show_recording'],
            show_numbers=data['show_numbers'],
            created_by=request.user,  # or request.user if you have authentication
            modified_by=request.user
        )

        return JsonResponse({"message": "Campaign created successfully!", "campaign_id": campaign.id,"success":True})

    return JsonResponse({"error": "Invalid request method","success":False, "error":True }, status=500)
    
## render view campaign page
@login_required(login_url="/login_home")    
def campaign_list(request):
    search_query = request.GET.get('q', '')  # Get the search query from the URL
    campaigns = Campaign.objects.filter(campaign_name__icontains=search_query).order_by('-id')  # Filter campaigns based on the search query
    
    paginator = Paginator(campaigns, 10)  # Show 10 campaigns per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'pages/campaign/list_campaign.html', context)


def edit_campaign():
    pass
def delete_campaign():
    pass

## render view campaign page
@login_required(login_url="/login_home") 
def contact_list(request, campaign_id):
    # Fetch the contact list based on the campaign_id
    contact_list = Campaign.objects.get(id=campaign_id).contact_list
    # Example: contact_list = get_contact_list_from_db(campaign_id)

    context = {"breadcrumb":{"title":"Create Agent","parent":"Pages", "child":"Sample Page"},"contact_list": contact_list,"campaign_id":campaign_id}
    return render(request, 'pages/campaign/contact_list.html', context)


# delete contact from campaign
@login_required(login_url="/login_home")
def delete_contact(request, campaign_id):
    if request.method == "POST":
        try:
            # Fetch the campaign based on the campaign_id
            campaign = get_object_or_404(Campaign, id=campaign_id)

            # Get the selected contact IDs from the request body
            data = json.loads(request.body)
            print(data)
            selected_contact_ids = data.get('contact_ids', [])

            if not selected_contact_ids:
                return JsonResponse({'message': 'No contact IDs provided.'}, status=400)

            # Fetch the contact_list (assumed to be a list of dictionaries)
            contact_list = campaign.contact_list

            # Remove contacts with matching IDs from the contact_list
            updated_contact_list = [
                contact for contact in contact_list if contact.get('contact_id') not in selected_contact_ids
            ]

            # Update the campaign's contact_list and save it
            campaign.contact_list = updated_contact_list
            campaign.save()

            return JsonResponse({'message': 'Contacts deleted successfully.',"success":True}, status=200)

        except Exception as e:
            return JsonResponse({'message': str(e),"success":False, "error":True}, status=500)

    return JsonResponse({'message': 'Invalid request method.',"error":True}, status=400)



######## start campaign
def start_campaign(request):
    if request.method == "POST":
        try:  
            request_body = json.loads(request.body)
            campaign_id = request_body['campaign_id']

            # read the values of the camaign
            campaign_obj = Campaign.objects.get(id=campaign_id)
            if not campaign_obj.contact_list:
                return JsonResponse({'message': 'No contacts present for this campaign',"success":False,"error":True}, status=200)
            
            # fetch the prompt
            prompt = campaign_obj.agent.agent_prompt

            # Iterate over the data
            contact_list = campaign_obj.contact_list
            voice_config = campaign_obj.agent.voice.voice_configuration
           
            # start a thread 
            wait_time_after_call,wait_time_after_5_calls = 1,1
            try:
                thread = threading.Thread(target=start_call_queue, args=(contact_list,voice_config,prompt,campaign_id,wait_time_after_call,wait_time_after_5_calls))
                thread.start()
            except Exception as err:
                print("error in campaign start: ", err)

            # set the status to ongoing 
            campaign_obj.status = "ongoing"
            campaign_obj.save()

            return JsonResponse({'message': 'Campaign started Successfully',"success":True,"error":False}, status=200)
        except Exception as e:
            print("error in start_campaig: ",e)
            pass


# call queue thread
def start_call_queue(contact_list,voice_config,prompt,campaign_id,wait_time_after_call,wait_time_after_5_calls):
    for call_details in contact_list:
        try:
            raw_text = prompt
            # format the prompt as the requirement
            print(raw_text)    
            formatted_prompt = prompt.format(**call_details)

            to_phone = call_details["contact_number"] # phone_number

            # call log creation
            call_log = call_details
            call_log["call_status"] = "not_started"
            call_log['campaign_id'] = campaign_id
            
            try:
                context={"prompt" : formatted_prompt}
                # hit a post request on api
                url = f"{settings.CALL_SERVER_BASE_URL}/start_call"

                payload = json.dumps({
                    "to_phone": to_phone,
                    "context":context,
                    "voice_configuration":voice_config
                })
                headers = {
                'Content-Type': 'application/json'
                }

                response = requests.request("POST", url, headers=headers, data=payload)

                # print(response.text)
                response = response.json()
                print("call_create api=> ", response)
                call_status_id = response["call_id"]
                call_log["call_id"] = call_status_id
                call_status = 'ongoing'

                if 'error' in response and response['error']: 
                    call_status = 'not_started'
                    
                call_status= "ongoing"
                

            except Exception as error:
                print("error in call create patient id --> ", to_phone,'\n',error)
                call_status = 'not_started'

            call_log["call_status"] =call_status

            # Create an instance of CallLogs with the dynamic fields
            call_log_entry = CallLogs(**call_log)

            # Save the call log to the database
            call_log_entry.save()
            mongo_id = call_log_entry.id

            # monitoring the call status
            monitor_thread = threading.Thread(target=monitor_call, args=( mongo_id,call_status_id,campaign_id))
            monitor_thread.start()
        except Exception as err:
            print(f"error while calling: {call_details['contact_number']} error- {err}")

 

# monitoring ongoing call
def monitor_call(mongo_id,call_status_id,campaign_id):
    call_status_current = ""
    not_started_count = 0
    
    while call_status_current not in ['ended', 'error']:
        time.sleep(1)  # wait for transcript
        # call_status_obj = call_client.calls.get_call(id=call_id)
        # call_status_current = call_status_obj.status

        # hit api to get status
        call_status_obj = get_current_call_status(call_status_id)
        call_status_current = call_status_obj['call_status']
        print('call_status_current --> ', call_status_current)

        if call_status_current == 'not_started':
            not_started_count += 1

            if not_started_count > 4:
                return False

        if call_status_current not in ['ended', 'error']:
            time.sleep(60)
        
        elif call_status_current == 'ended':
            time.sleep(2)
            # transcript = call_status_obj.transcript
            transcript = call_status_obj['transcript']
            # call_start = str(call_status_obj.start_time)[:19]
            # call_end = str(call_status_obj.end_time)[:19]

            duration = 0
            try:
                # Convert strings to datetime objects
                start_time = datetime.fromisoformat(call_start)  # Remove 'Z' from end
                end_time = datetime.fromisoformat(call_end)      # Remove 'Z' from end

                # Calculate the difference
                time_difference = end_time - start_time

                # Extract the difference in seconds
                duration = int(time_difference.total_seconds())
            except:
                pass

            # import pdb;pdb.set_trace()
            entities = extract_entities_from_transcript(transcript)
            summary = ""
            status = "Completed"
            try:
                # updating the summary and call status
                entities = entities.replace("```json", "").replace("```", "").replace("\n", "")
                if entities:
                    entities = json.loads(entities)
                    summary = entities["summary"]
                    status = entities["call_status"]
                    if 'fail' in status.lower():
                        status = "Failure"
            except Exception as err:
                print("Error generating summary: ", err)

            ## transcript save
            transcript_obj = Transcript()
            transcript_obj.campaign_id =  campaign_id
            transcript_obj.call_logs = call_status_id

            
            try:
                qa_analysis =analyze_call(
                    {
                        "summary": summary,
                        "transcript": transcript,
                     }
                )
 
                transcript_obj.qa_analysis = qa_analysis
            except Exception as err:
                print("print error ", err)    
            transcript_obj.save()

            #### update call log mongo
            updated_fields = {
                "call_status": "completed",
                "call_duration": 0  # Example of updating multiple fields
            }

            updated_call_log = update_call_log(mongo_id, updated_fields)
            print(updated_call_log)
            return True

        elif call_status_current == 'error':
             
            # Fetch all calls for the patient
 
            #### update call log mongo
            updated_fields = {
                "call_status": "not_started",
                "call_duration": 0  # Example of updating multiple fields
            }

            updated_call_log = update_call_log(mongo_id, updated_fields)
            print(updated_call_log)

 
  
            return True
    return True


"""
function to fetch call status
"""
def get_current_call_status(call_id):
    try:
        # hit a post request on api
        url = f"{settings.CALL_SERVER_BASE_URL}/call_status"

   

        response = requests.get(url,params={"call_id":call_id})

        # print(response.text)
        response = response.json()
        print(response)
        call_status = response["call_status"]
        call_uuid = response["call_id"]
        print(f"call_status => {call_status}, call_uuid => {call_uuid}")
        return response
    except Exception as error:
        print("error in call get_current_call_status call id --> ", call_id)
        return {}


## creating summary from call
def extract_entities_from_transcript(transcript):

    # Define your API key
    api_key = os.getenv("OPENAI_API_KEY")

    # Define the endpoint URL
    url = "https://api.openai.com/v1/chat/completions"

    prompt ="""
            Below is the transcript of conversation between a agent and an employee in the insurance facility, based on the conversation between them about the claim create a short summary about the call.
            The summary will contain few sentences describing the agent's perspective on the call , and also mention the call refercne number and facility name as well as the call receivers name
            Along with the summary also give the "call_status" i.e. whether the call was successful in retrieving claim status or not.
            Note:
                The summary must start with Service Date and Billed Amount.
                while creating summary don't use agent's name instead use 'I' as the summary is based on agent's perspective.
                Summary must contain call reference number at the end of conversation if its not present write NA.
                The call reference number must be in integer form i.e, 123 not in words  form like one,two,three .
                You are calling from wound technology not to wound technology so in the summary never mention the you Called wound technology.
                In case the call dowes not get connected to a representative after navigating the ivr, specify in the summary that you were not able to connect to a facility representative, in the case the claim_status will be "failure".
                In case you have called the wrong facility mention the same in summary report, in the case the claim_status will be "failure".
                The call_status will be considered as successfull if the calim status for the patient was fetched successfully.

                The output must be a json object with two keys "summary" and "call_status" , these two keys must be there with the same case.
                

            sample output summary (call concluded successfully):
                {
                    "call_status":"Completed",
                    "summary": "I called to insurance @<facility contact> spoke with rep <call receiver name> to check denied So as per rep checking claim is denied because services are not covered under the member's benefit plan. Rep informed that she need more 7-10 business days to inquiry for denied because claim denied incorrectly.call ref #<call refernce_numver> claim number #<claim_number>"
                }

            sample output summary (call was not successfull):
                {
                    "call_status":"Failed",
                    "summary": "I called to insurance @<facility contact> but I was not able to connect to a representative."
                }

            Transcription:
                    
                %s

            """% (transcript)

    # Define parameters
    data = {
            "model":"gpt-4o",
            # "model":"gpt-3.5-turbo",
            "max_tokens": 2048,  # Maximum number of tokens to generate
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant whose task is to generate the summary and call conclusion from given conversation."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ]        
        }

        # Define headers with your API key
    headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # Make the request
    response = requests.post(url, json=data, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the completion
        # print(response.json()['choices'][0]["message"] )
        # return {"status":200 ,"message":response.json()['choices'][0]["message"]['content'] }
        return response.json()['choices'][0]["message"]['content']
    else:
        print("Error:", response.status_code)
        print(response.json())
        return response.json()    
    

############################## QA APIS ####################
def analyze_call(request_body):
    try:
        call_parameters = get_call_parameters()
        summary = request_body['summary']
        transcript = request_body['transcript']

        process_description = """
            Process: RCM
            The RCM process dels the the lifecycle ...
            """


        llm_prompt = """
                You are a QA anlyst whose job analyze the call that an associate handled and judge the call quality.
                The quality will be judged based on the parameters given to you in a json format, each parameter has to judged accordingly.

                The Parameters will depend upon the process.
                %s

                The inputs are as follows:
                parameters: The calling parmaeters that the acssociate must meet during the call.
                summary: The short summary about the things that happend in the call.
                Transcript: The full conversation that took place between the handled

                Remember that you are only supposed to only judge the acossiates contents and not the facility employee's content
                The response must be in json format for each and every parameter. The response will contain two keys in list of dictionary "parameter" and "result"
                The result key will contain only "met" or "not met" value depending upon the call quality.
                example:
                [
                    {
                        "parameter":"..."
                        "result": "met"
                    },
                    {
                        "parameter":"..."
                        "result": "not met"
                    }
                ]
        """%(process_description)

        parameter_prompt = f"""
            call_parameters: {call_parameters}

            summary: {summary}

            Transcript: {transcript}    
        """
        # Define your API key
        api_key = os.getenv("OPENAI_API_KEY")

        # Define the endpoint URL
        url = "https://api.openai.com/v1/chat/completions"
        # Define parameters
        data = {
                "model":"gpt-4o",
                # "model":"gpt-3.5-turbo",
                "max_tokens": 2048,  # Maximum number of tokens to generate
                "messages": [
                    {
                        "role": "system",
                        "content": llm_prompt
                    },
                    {
                        "role":"user",
                        "content":parameter_prompt
                    }
                ]        
            }

            # Define headers with your API key
        headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            # Make the request
        response = requests.post(url, json=data, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Print the completion
            return response.json()['choices'][0]["message"]['content']
        else:
            print("Error:", response.status_code)
            print(response.json())
            return response.json()    
    except Exception as err:
        print("Error in analyze_call: ",err)

def get_call_parameters():
    parameters = [
        {
            "calling_parameters": "Did the associate create clear and concise notes? (Status notes and facility notes)",
            "description": "Agent is supposed to update the notes on work order correct and precisely as per the the conversation with COR"
        },
        {
            "calling_parameters": "Did the associate take the appropriate steps to speak to a live contact and request for the office manager/supervisor when necessary? Exhaust all options",
            "description": "Was the call made to right number/location. Need to spend min 7 minutes on the call/hold/wait time in case of no live contact. Also if we dialed alternate numbers to get a contact while doing exhaust"
        },
        {
            "calling_parameters": "Did the associate send/resend the request using the correct mode when necessary? (Fax / Mail / Email / Copy Service Portal)",
            "description": "Is the request sent/resent when we are given fax/email/mailing address by facility. Also, in case of 3 failed attempts of live contact/update, we are supposed to resend the request. When we are doing exhaust, if we have an alternate email address, we should send the request accordingly"
        },
        {
            "calling_parameters": "Did the associate ask all the necessary questions to decrease the cycle time?",
            "description": "Were all the actions taken to help in reducing the TAT and was research done accordingly on the request "
        },
        {
            "calling_parameters": "Did the associate leave a message in a way the facility could understand per scenario of the request and document the same on the notes? (Clear and slow)",
            "description": "Were all the details given on voicemail, was the rate of speech, pronunciation clear"
        },
        {
            "calling_parameters": "Did the associate set up a follow up reminder as an when required or call the facility when it\\'s required?",
            "description": "Agents need to setup the reminder to call/follow up if the facility is closed during working hours/ execpt Friday-second half. Also, if the reminer is set when facility asked for a call back same day or in same week"
        },
        {
            "calling_parameters": "Did the associate escalate the request as per the process?",
            "description": "If we could not get any status update in a month, OR if the request is rejected and if agent does not have acess to rectify the request- we need send the request to service rep. "
        },
        {
            "calling_parameters": "Did the associate check the Record Request (RR) tab to eliminate the possibility of duplicate order? If identified as duplicate order, did the associate take the necessary action to address the issue?",
            "description": "We need to check if the request is duplicate, if so, take appropriate action to close the request. Necessary research done to reduce the TAT and close the order"
        },
        {
            "calling_parameters": "Did the associate probe accordingly as per the previous notes?",
            "description": "Did the agent read the previous notes and asked appropriate questions regarding the work order"
        },
        {
            "calling_parameters": "Did the associate communicate in a way the facility could understand and display professional behavior over the call?",
            "description": "Was the agent professional, was the facility rep able to understand the agent, regional language recorded on call, loud background noice captured on call"
        },
        {
            "calling_parameters": "Did the associate do anything which was detrimental to the facility or the process?",
            "description": "Fatal error- any rude behaivior, work avoidance, call avoidance, taken productivity without working on the order, PHI breach, calling directly to client or patient for status update, etc"
        },
        {
            "calling_parameters": "Did the associate open a scanning issue as per the process?",
            "description": "If facility states that they have sent the records, we should check with the scanning team by opening the scanning process, agent is supposed to ask to resend the records if we have not received it"
        },
        {
            "calling_parameters": "Did the associate introduce self-using his/her name, the company\\'s name and the purpose of calling?",
            "description": "Did the agent mention his/her name and company's name clearly at the start of the call"
        },
        {
            "calling_parameters": "Did the associate follow the right payment process?",
            "description": "Did the agent void and reissue the check when the facility has told to send another check payment as the 1st check payment was not received "
        },
        {
            "calling_parameters": "Did the associate ask necessary questions to the provider when they rejected our authorization as an invalid authorization?",
            "description": "Did the agent probe regarding the rejection reason when it was told by the facility rep that the authorization or the request is not correct/valid"
        },
        {
            "calling_parameters": "Did the associate close the call as per process?",
            "description": "Did the agent say plesantries like thank you at the end of the call"
        }
    ]
    
    return parameters


def update_call_log(call_id, updated_fields):
    try:
        # Fetch the document using the call_id
        call_log = CallLogs.objects.get(id=call_id)

        # Update the specified fields
        for key, value in updated_fields.items():
            setattr(call_log, key, value)

        # Save the updated document back to the database
        call_log.save()

        return call_log  # Return the updated document, if needed

    except Exception as err:
        print("CallLog with the given ID does not exist.")
        return None  # or handle as appropriate

"""
Display call logs of a perticular campaign
"""
def list_call_logs(request):
    if request.method == "GET":
        try:
            campaign_list = Campaign.objects.filter(is_delete=False)
            if not request.user.is_superuser:
                campaign_list = campaign_list.filter(organisation_name=request.user.organisation_name)

            campaign_list = list(campaign_list.values("id", "campaign_name"))

            campaign_id = request.GET.get('campaign_id',0)
            call_status = request.GET.get('call_status',"ongoing")
            call_logs_data = []
            dynamic_columns = []
            total_pages = 0
            page = 1
            paginated_logs =[]

            if campaign_id:
                call_logs = CallLogs.objects(campaign_id=int(campaign_id)).order_by('-created_at')
                if call_status:
                    call_logs = call_logs.filter(call_status=call_status)

                # Pagination logic
                page = int(request.GET.get('page', 1))
                per_page = int(request.GET.get('per_page', 10))
                per_page=1
                paginator = Paginator(call_logs, per_page)
                paginated_logs = paginator.get_page(page)
                total_pages = paginator.num_pages
                print("num pages" ,total_pages)
                call_logs_data = [json.loads(log.to_json()) for log in paginated_logs]
                
                # Extract dynamic columns from the first log
                if call_logs_data:
                    dynamic_columns = list(call_logs_data[0].keys())

            context = {
                "breadcrumb": {"title": "View Call Logs", "parent": "Pages", "child": "Call Logs"},
                "call_logs_data": call_logs_data,
                "campaign_list": campaign_list,
                "call_status":call_status,
                "dynamic_columns": dynamic_columns,
                "total_pages": total_pages,
                "success": True,
                "page": page,
                "paginated_logs":paginated_logs,
                "campaign_id":str(campaign_id)
            }

            return render(request, 'pages/campaign/call_logs.html', context)

        except Exception as error:
            print("error in list_call_logs: ", error)
            return JsonResponse({"error": "No call logs found for this campaign"}, status=404)

        
    elif request.method == "POST":
        return JsonResponse({"error": "POST method not supported for this endpoint"}, status=405)


###################################################################################
########################## Call Details ##########################################

def fetch_call_details(request):
    try:
        request_body = json.loads(request.body)
        campaign_id, mongo_id, call_id = request_body['campaign_id'],request_body['mongo_id'], request_body['call_id']

        response = {}
        # fetch transcript and summary
        transcript_data =Transcript.objects.get(call_logs=call_id,campaign_id= campaign_id) 
        transcript_obj = {}
        try:
            transcript_obj["transcript"] = format_transcript(transcript_data.transcript)
        except:
            transcript_obj["transcript"] = ""

        transcript_obj['summary'] = transcript_data.summary

        # fetch telephony
        campaign_object = Campaign.objects.get(id=campaign_id)
        telephony_data = campaign_object.provider.provider_name

        transcript_obj['telephony_name']  = telephony_data
        transcript_obj["transcript_obj_id"] = transcript_data.id

        return JsonResponse({"error": False, "success":True, "message":"call_details fetched successfully ","data":transcript_obj}, status=200)

        
    except Exception as err:
        print("error in fetch call details: ",err)
        return JsonResponse({"error": True, "success":False, "message":"Error fetching call details "}, status=500)

## functio to format transctipt
def format_transcript(transcript):
    lines = transcript.split('\n')
    formatted_lines = []
    for line in lines:
        # Wrap timestamp with span
        timestamp_end = line.find(']')
        if timestamp_end != -1:
            timestamp = line[:timestamp_end+1]
            rest_of_line = line[timestamp_end+1:]
            line = f'<span class="timestamp">{timestamp}</span><br>{rest_of_line}'

        # Wrap HUMAN with span
        if 'HUMAN:' in line:
            line = line.replace('HUMAN:', '<span class="human" style="color:green">HUMAN:</span>')
        if 'BOT:' in line:            
            line = line.replace('BOT:', '<span class="bot" style="color:red">BOT:</span>')

        formatted_lines.append(line)
    return '\n'.join(formatted_lines)


def fetch_audio(request):
    try:
        data = json.loads(request.body)  # Get JSON data from the request
        call_id = data['call_id']
        telephony_name = data['telephony_name']
        print("call_id: ", call_id,'telephony_name: ',telephony_name)
        

        # Twilio account credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID') 
        auth_token =  os.getenv('TWILIO_AUTH_TOKEN')  # Replace with your Twilio Auth Token
            
        if not call_id:
            return JsonResponse({"error": True, "success":False, "message":"No call_id provided"}, status=400)
        
        if telephony_name == "twilio" or telephony_name == "telnyx" :  # hardocded for testing
            # Construct the URL for the Call API
            base_url = 'https://api.twilio.com'
            url= f'{base_url}/2010-04-01/Accounts/{account_sid}/Calls/{call_id}/Recordings.json'
            
 
            response = requests.get(url, auth=HTTPBasicAuth(account_sid, auth_token))

            # Parse the response JSON to get the recording URL
            recordings_data = response.json()
            recordings_list = recordings_data.get('recordings', [])
            
            recording_url = None
            if recordings_list:
                recording_sid = recordings_list[0]['sid']
                recording_url = f'{base_url}/2010-04-01/Accounts/{account_sid}/Recordings/{recording_sid}.mp3'
                print(f'Recording URL: {recording_url}')

                response = requests.get(recording_url)
                if response.status_code == 200:
                    # audio_stream = io.BytesIO(response.content)
                    # return send_file(audio_stream, mimetype='audio/mpeg', as_attachment=False, download_name=f'{call_id}_audio.mp3')
                    audio_stream = io.BytesIO(response.content)
                    audio_stream.seek(0)  # Reset stream position to the start
                    return FileResponse(audio_stream, as_attachment=False, content_type='audio/mpeg')

                else:
                    return "Failed to fetch the recording.", 500
            else:
                print('No recordings found for the call.')
                return "Failed to fetch the recording.", 500

        # if response.ok:
        #     # Create an in-memory byte-stream for the audio file
        #     audio_stream = BytesIO(response.content)
        #     return send_file(audio_stream, mimetype='audio/mpeg', as_attachment=False, download_name=f'{call_id}_audio.mp3')
        # else:
        #     return jsonify({'success': False, 'message': 'Failed to fetch audio'}), response.status_code
    
    except Exception as e:
        print(f"Error in fetch_audio: {e}")
        # return jsonify({'success': False, 'message': str(e)}), 500        

"""
 Funtions to edit summary and transcript
"""
def edit_summary(request):
    try:
        # import pdb;pdb.set_trace()
        request_body = request.POST.dict()
        status_filter = request_body['status']
        campaign_id = request_body['campaign_id']
        edit_summary_id = request_body['id']
        new_summary = request_body['edited_summary']
        # update transcript
        transcript_obj = Transcript.objects.get(id= edit_summary_id)     
        transcript_obj.summary = new_summary
        transcript_obj.save()

        # Build the URL with query parameters
        url = reverse('list_call_logs')  # Gets the URL path for the 'edit_summary' route
        query_params = f'?status_filter={status_filter}&campaign_id={campaign_id}'
        

        return redirect(f'{url}{query_params}')
    
    except Exception as error:
        print(f"Error editing call: {error}")
        return redirect('/')
    

def edit_transcript(request):
    try:
        request_body = request.POST.dict()
        status_filter,campaign_id = request_body['status'], request_body['campaign_id']
        edit_transcript_id = request_body['id']
        new_transcript = request_body['edited_transcript']
        # update transcript
        transcript_obj = Transcript.objects.get(id= edit_transcript_id)
        transcript_obj.transcript = new_transcript
        transcript_obj.save()

        # Build the URL with query parameters
        url = reverse('list_call_logs')  # Gets the URL path for the 'edit_summary' route
        query_params = f'?status_filter={status_filter}&campaign_id={campaign_id}'

        return redirect(f'{url}{query_params}')                
    except Exception as error:
        print("Error editing call: ",error)
        return redirect('/')
 