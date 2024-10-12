from django.shortcuts import render,redirect
from django.contrib import messages
from django.http.response import HttpResponseRedirect,JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from zonoapp.models import User
from voice.models import Voice
from agent.models import Agent
from .models import Campaign, Transcript,CallLogs, ContactList, ScheduleCampaign
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
import csv
from qa_parameters.models import QAParameters

## render create campaign page
@login_required(login_url="/login_home")
def create_campaign(request):
    if request.method == "GET":
        try:
            telephony_providers_list =  Provider.objects.filter(provider_type="telephony")
            if request.user.is_superuser:
                org_names = User.objects.filter(is_deleted=False).values_list('organisation_name',flat=True)
            else:
                org_names = User.objects.filter(is_deleted=False,username=request.user).values_list('organisation_name',flat=True)
            print('org_names ',org_names)

            available_agents = Agent.objects.filter(is_deleted=False)
            
            #### QA parameters list
            qa_parameters = QAParameters.objects.filter(is_deleted=False,organisation_name__in = org_names)
            
            if not request.user.is_superuser:
                available_agents = available_agents.filter(organisation_name__in=org_names)
            print('available_agents ',available_agents)
            # available_voice = Agent.objects.filter(is_deleted=False)

            context = {"breadcrumb":{"title":"Create Campaign","parent":"Pages", "child":"Create Campaign"},
                    "telephony_providers_list":telephony_providers_list,"org_names":org_names,"qa_parameters":qa_parameters,
                    "available_agents":available_agents
                    }   
            
            return render(request,'pages/campaign/create_campaign.html',context)
            
        except Exception as error :
            print("error in create_campaign :  ",error)
            return render(request,'pages/error-pages/error-500.html',{"error":error})

    elif request.method == "POST":
        try:
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
                # contact_list = new_contact_list,  # removed old logic of single list
                agent=agent,
                summarization_prompt=data['summarization_prompt'],
                qa_parameters_id= data["qa_parameters_list"],
                show_recording=data['show_recording'],
                show_numbers=data['show_numbers'],
    
            )

            #######################################################
            """ #### New Logic for adding contact list ######## """
            campaign_id = campaign.id

            # Save the campaign contact list and mark it as active
            campaign_contact_list = ContactList.objects.create(
                list_name="default",
                campaign_id=campaign_id,
                contact_list=new_contact_list,
                is_active=True,  # Make it active by default
                organisation_name=data['organisation_name'],
                created_by="system",
                modified_by="system",
            )

            # Update the campaign with the contact_list_id
            campaign.contact_list_id = campaign_contact_list.id
            campaign.save()
            #######################################################
            return JsonResponse({"message": "Campaign created successfully!", "campaign_id": campaign.id,"success":True})
        except Exception as error :
            print("error in create_campaign :  ",error)
            return render(request,'pages/error-pages/error-500.html',{"error":error})
    return JsonResponse({"error": "Invalid request method","success":False, "error":True }, status=500)
    
############ upload new contacts csv #######
def upload_contact_list(request, campaign_id):
    if request.method == "POST":

        # Get the uploaded file
        csv_file = request.FILES.get('csvFile')
        list_name = request.POST.get('list_name')
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'status': 'error', 'message': 'Invalid file format. Please upload a CSV file.'})

        # Get the contact list structure
        contact_list =  ContactList.objects.filter(campaign_id=campaign_id,is_deleted=False,is_active=True).first()
        if contact_list.contact_list:
            keys_to_match =  list(contact_list.contact_list[0].keys())
            try:
                keys_to_match.remove("contact_id")
            except:
                pass # removing the auto generated_column
        else:
            keys_to_match = []
        current_columns = keys_to_match   
        print("current_columns ==> ",current_columns)

        # Parse and validate the CSV file
        try:
            csv_data = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
            uploaded_columns = csv_data.fieldnames
            
            # Check if columns match
            if set(uploaded_columns) != set(current_columns):
                return JsonResponse({'status': 'error', 'message': 'CSV columns do not match the existing contact list.'})

            # Save the uploaded data to new contact list



            new_contact_list = [row for row in csv_data]
            new_contact_list_refined = []
            for contact in new_contact_list:
                # add a unique identifiier to each contact
                contact["contact_id"] = "contact_"+str(uuid.uuid4().hex)
                new_contact_list_refined.append(contact)

            contact_list = ContactList( 
                list_name=list_name,
                campaign_id=campaign_id,
                is_active=False,  # Make it active by default
                organisation_name=str(request.user.organisation_name),
                created_by="system",
                contact_list = new_contact_list_refined,
                modified_by="system"
            )

            contact_list.save()

            return JsonResponse({'status': 'success', 'message': 'Contact list uploaded successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)    


## render view campaign page
@login_required(login_url="/login_home")    
def campaign_list(request):
    try :
        search_query = request.GET.get('q', '')  # Get the search query from the URL
        campaigns = Campaign.objects.filter(campaign_name__icontains=search_query).order_by('-id')  # Filter campaigns based on the search query
        
        paginator = Paginator(campaigns, 10)  # Show 10 campaigns per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Add custom key-value pairs to the campaigns in page_obj after pagination
        for campaign in page_obj:
            if campaign.is_schedule:
                # find out schedule_date
                schedule_obj = ScheduleCampaign.objects.filter(campaign=campaign,is_finished=False).first().schedule_date
                campaign.scheduled_date = schedule_obj
            else:
                campaign.scheduled_date = ""

        context = {
            "breadcrumb":{"title":"Campaign Management","parent":"Pages", "child":"Campaign Management"},
            'page_obj': page_obj,
            'search_query': search_query,
        }
        return render(request, 'pages/campaign/list_campaign.html', context)
    except Exception as error :
            print("error in create_campaign :  ",error)
            return render(request,'pages/error-pages/error-500.html',{})


def edit_campaign():
    pass
def delete_campaign():
    pass

## render view campaign page
@login_required(login_url="/login_home") 
def contact_list(request, campaign_id):
    if request.method=="GET":
        try:
            # Fetch the contact list based on the campaign_id
            campaign = Campaign.objects.get(id=campaign_id)
            all_contact_list_names = ContactList.objects.filter(is_deleted = False, campaign=campaign).values_list('list_name','id')

            # import pdb;pdb.set_trace()
            contact_list = ContactList.objects.filter(is_deleted = False, campaign=campaign)
            # select the specfic list from a campaign
            selected_list = request.GET.get("selected_contact_list")

            if selected_list:
                contact_list = contact_list.filter(id = selected_list)
                contact_list_id = contact_list[0].id
                is_active = contact_list[0].is_active
                contact_list = list(contact_list[0].contact_list)
            else:
                if contact_list and all_contact_list_names: # filter only is main contact list is not empty
                    contact_list = contact_list.filter(id = all_contact_list_names[0][1] ) # id of the contact_list
                    contact_list_id = contact_list[0].id
                    is_active = contact_list[0].is_active
                    contact_list = list(contact_list[0].contact_list)

            print("final_conact_list_b4 uload + ",contact_list)
            context = {"breadcrumb":{"title":"Contact List","parent":"Pages", "child":"Contact List"},"contact_list": contact_list,"campaign_id":campaign_id,
                        "all_contact_list_names":all_contact_list_names, "selected_contact_list":selected_list,"contact_list_id":contact_list_id,
                        "is_active":is_active
                    }
            
            return render(request, 'pages/campaign/contact_list.html', context)
        
        except Exception as err:
            print("error fetching contact list: ",err)
            return render(request, 'pages/error-pages/error-500.html', {})
        
    if request.method == "POST":
        request_body = json.loads(request.body)
        print(request_body)
        # fetch the campaign_id and contact_list_id
        contact_list_id = request_body.get("contact_list_id")
        campaign_id = request_body.get("campaign_id")

        if contact_list_id and campaign_id:
            # Mark all contact lists as inactive for this campaign
            ContactList.objects.filter(campaign_id=campaign_id).update(is_active=False)

            # Set the selected contact list as active
            contact_list = ContactList.objects.get(id=contact_list_id)
            contact_list.is_active = True
            contact_list.save()

            return JsonResponse({'status': 'success', 'message': 'Contact list marked as active.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid data.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)



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
            contact_list = campaign.contact_list.contact_list

            # Remove contacts with matching IDs from the contact_list
            updated_contact_list = [
                contact for contact in contact_list if contact.get('contact_id') not in selected_contact_ids
            ]

            # Update the campaign's contact_list and save it
            # campaign.contact_list.contact_list = updated_contact_list
            # campaign.save()

            contact_list_obj = campaign.contact_list  
            contact_list_obj.contact_list = updated_contact_list  # Assuming contact_list is a JSON field or similar
            contact_list_obj.save()  # Save the updated list to the database

            return JsonResponse({'message': 'Contacts deleted successfully.',"success":True}, status=200)

        except Exception as e:
            print(e)
            return JsonResponse({'message': str(e),"success":False, "error":True}, status=500)

    return JsonResponse({'message': 'Invalid request method.',"error":True}, status=400)



######## start campaign
def start_campaign(request):
    if request.method == "POST":
        try:  
            request_body = json.loads(request.body)
            campaign_id = request_body['campaign_id']
            campaign_obj = Campaign.objects.get(id=campaign_id)
            if not campaign_obj.contact_list:
                return JsonResponse({'message': 'No contacts present for this campaign',"success":False,"error":True}, status=200)

            prompt = campaign_obj.agent.agent_prompt

            # Iterate over the data
            contact_list = campaign_obj.contact_list.contact_list
            voice_config = campaign_obj.agent.voice.voice_configuration
            qa_params, summarization_prompt = campaign_obj.qa_parameters.qa_parameters, campaign_obj.summarization_prompt

            # start a thread 
            wait_time_after_call,wait_time_after_5_calls = 1,1
            try:
                thread = threading.Thread(target=start_call_queue, args=(contact_list, voice_config,prompt,campaign_id,wait_time_after_call,wait_time_after_5_calls,qa_params, summarization_prompt, campaign_obj.organisation_name))
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
def start_call_queue(contact_list,voice_config,prompt,campaign_id,wait_time_after_call,wait_time_after_5_calls,qa_params, summarization_prompt):
    # if the campaign is scheduled mark is_schedule as false as the campaign is already started
    campaign_obj = Campaign.objects.get(id=campaign_id)
    try:
        if campaign_obj.is_schedule:
            campaign_obj.is_schedule=False
            campaign_obj.save()

            # update the scheduled table
            schedule_obj = ScheduleCampaign.objects.filter(campaign_id=campaign_id,is_finished=False,is_ongoing=False).first()
            schedule_obj.is_ongoing=True
            schedule_obj.save()

        else:
            pass

    except Exception as error:
        print("error updating scheduled: ",error) 
    print(contact_list  )
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

            call_log["call_status"] = call_status
            call_log["start_time"] = datetime.now()
            call_log["end_time"] = None

            # Create an instance of CallLogs with the dynamic fields
            call_log_entry = CallLogs(**call_log)

            # Save the call log to the database
            call_log_entry.save()
            mongo_id = call_log_entry.id

            # monitoring the call status
            monitor_thread = threading.Thread(target=monitor_call, args=( mongo_id,call_status_id,campaign_id,qa_params, summarization_prompt,call_log["start_time"]))
            monitor_thread.start()
        except Exception as err:
            print(f"error while calling: {call_details['contact_number']} error- {err}")

    # once all the calls are over update the campaign object to completed
        campaign_obj.status="completed"
        campaign_obj.save()
    # once all the calls are over update the schedule campaign object to completed
    try:
        # update the scheduled table
        schedule_obj = ScheduleCampaign.objects.filter(campaign_id=campaign_id, is_ongoing=True).first()
        schedule_obj.is_ongoing=False
        schedule_obj.is_finished=True
        schedule_obj.save()

    except Exception as err:
        print("error while updating schedule campaign object: ",err)
    return True


# monitoring ongoing call
def monitor_call(mongo_id,call_status_id,campaign_id,qa_params, summarization_prompt,call_start_time):
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
            call_end = datetime.now()

            duration = 0
            end_time = datetime.fromisoformat(str(call_end))
            try:
                # Convert strings to datetime objects
                start_time = datetime.fromisoformat(str(call_start_time))  # Remove 'Z' from end
                # end_time = datetime.fromisoformat(str(call_end))      # Remove 'Z' from end

                # Calculate the difference
                time_difference = end_time - start_time

                # Extract the difference in seconds
                duration = int(time_difference.total_seconds())
            except:
                pass

            # import pdb;pdb.set_trace()
            summary = ""

            ######### Perform the call summary if the prompt is given else skip ########
            if summarization_prompt:
                status = "Completed"
                try:
                    entities = extract_entities_from_transcript(transcript,summarization_prompt)
                    # updating the summary and call status
                    entities = entities.replace("```json", "").replace("```", "").replace("\n", "")
                    if entities:
                        entities = json.loads(entities)
                        summary = entities["summary"]
                        status = entities["call_status"]
                        # if 'fail' in status.lower():
                        #     status = "Failure"
                except Exception as err:
                    print("Error generating summary: ", err)
            #################################################################

            ## transcript save
            transcript_obj = Transcript()
            transcript_obj.campaign_id =  campaign_id
            transcript_obj.call_logs = call_status_id
            transcript_obj.summary = summary
            transcript_obj.transcript = transcript
            
            ############### Perform the call QA if the qa_params is given else skip ########
            try:
                ## QA parameters
                qa_analysis =analyze_call( { "summary": summary, "transcript": transcript,"qa_params":qa_params } )
                transcript_obj.qa_analysis = qa_analysis
            except Exception as err:
                print("print error ", err)    
            
            transcript_obj.save()

            #### update call log mongo
            updated_fields = {
                "call_status": "completed",
                "end_time":end_time,
                "call_duration": duration  # Example of updating multiple fields
            }

            updated_call_log = update_call_log(mongo_id, updated_fields)
            return True

        elif call_status_current == 'error':
             
            # Fetch all calls for the patient
            end_time = datetime.fromisoformat(str(call_end))
            #### update call log mongo
            updated_fields = {
                "call_status": "not_started",
                "end_time":end_time,
                "call_duration": 0  # Example of updating multiple fields
            }

            updated_call_log = update_call_log(mongo_id, updated_fields)

 
  
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
        call_status = response["call_status"]
        call_uuid = response["call_id"]
        return response
    except Exception as error:
        print("error in call get_current_call_status call id --> ", call_id)
        return {}


## creating summary from call
def extract_entities_from_transcript(transcript,summarization_prompt):

    # Define your API key
    api_key = os.getenv("OPENAI_API_KEY")

    # Define the endpoint URL
    url = "https://api.openai.com/v1/chat/completions"

    prompt = """
            %s

            sample output summary (call concluded successfully):
                {
                    "call_status":"Completed",
                    "summary": "I called to insurance @<facility contact> spoke with rep <call receiver name> to check denied So as per rep checking claim is denied because services are not covered under the member's benefit plan. Rep informed that she need more 7-10 business days to inquiry for denied because claim denied incorrectly.call ref #<call refernce_numver> claim number #<claim_number>"
                }

            sample output summary (call was not successful):
                {
                    "call_status":"Failed",
                    "summary": "I called to insurance @<facility contact> but I was not able to connect to a representative."
                }

            Transcription:
                
                %s
            """ % (summarization_prompt, transcript)

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
        # call_parameters = get_call_parameters()
        call_parameters = request_body['qa_params']
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
@login_required(login_url="/login_home")
def list_call_logs(request):
    if request.method == "GET":
        try:
            campaign_list = Campaign.objects.filter(is_delete=False)
            if not request.user.is_superuser:
                campaign_list = campaign_list.filter(organisation_name=request.user.organisation_name)

            campaign_list = list(campaign_list.values("id", "campaign_name"))

            campaign_id = request.GET.get('campaign_id',0)
            if  request.user.is_superuser or request.user.role.role == "QA" or request.user.role.role == "Admin":
                call_status = request.GET.get('call_status',"completed")
            else:
                call_status = request.GET.get('call_status', "ongoing")
            print("call_status", call_status)
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

        except Exception as error :
            print("error in no call log found :  ",error)
            return render(request,'pages/error-pages/error-500.html',{"error":error})

        
    elif request.method == "POST":
        print("POST method not supported for this endpoint :",error)
        return render(request,'pages/error-pages/error-500.html',{"error":error})


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
        try:
            transcript_obj['qa_analysis'] = create_html_component_with_div(json.loads(transcript_data.qa_analysis.replace("```json","").replace("```","")))
        except Exception:
            transcript_obj['qa_analysis'] = create_html_component_with_div(transcript_data.qa_analysis)
            print("transcript_obj=================>", transcript_data.qa_analysis)
        return JsonResponse({"error": False, "success":True, "message":"call_details fetched successfully ","data":transcript_obj}, status=200)

        
    except Exception as err:
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

def create_html_component_with_div(json_list):
    print("json_list=======", json_list)
    # HTML structure
    html_content = ""
    id_count = 1
    for item in json_list:
        parameter = item.get('parameter', '')
        result = item.get('result', '')
        html_content += "<div>\n"
        html_content += f"""  <span id="params{id_count}" name="params{id_count}">{parameter}</span>\n"""
        html_content += """<br>
        <select id="result{id_count}" name="{parameter}">
            <option value="met" {met_selected}>Met</option>
            <option value="not met" {not_met_selected}>Not Met</option>
        </select>
        """.format(
            met_selected="selected" if result == "met" else "",
            not_met_selected="selected" if result == "not met" else "",
            id_count=id_count,
            parameter=parameter
        )
        html_content += "</div><br>\n"
        id_count += 1


    return html_content

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
        page = request_body['page']

        # Build the URL with query parameters
        url = reverse('list_call_logs')  # Gets the URL path for the 'edit_summary' route
        query_params = f'?call_status={status_filter.lower()}&campaign_id={campaign_id}&&page={page}&per_page=10'

        

        return redirect(f'{url}{query_params}')
    
    except Exception as error:
        print(f"Error editing call: {error}")
        return redirect('/')
    

def editQa(request):
    try:
        request_body = request.POST.dict()
        exclude_keys = {'csrfmiddlewaretoken', 'id', 'campaign_id', 'search', 'selected_agent', 'sort_order', 'sort_column', 'page', 'call_status', 'status'}
        formatted_list = [{'parameter': key, 'result': value} for key, value in request_body.items() if key not in exclude_keys]
        status_filter = request_body['status']
        campaign_id = request_body['campaign_id']
        edit_summary_id = request_body['id']
        transcript_obj = Transcript.objects.get(id= edit_summary_id)     
        transcript_obj.qa_analysis = formatted_list
        transcript_obj.save()
        page = request_body['page']

        url = reverse('list_call_logs')  
        query_params = f'?call_status={status_filter.lower()}&campaign_id={campaign_id}&&page={page}&per_page=10'
        

        return redirect(f'{url}{query_params}')

    except Exception as e:
        print(e)

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
        page = request_body['page']
        print(page)

        query_params = f'?call_status={status_filter.lower()}&campaign_id={campaign_id}&&page={page}&per_page=10'

        print(f"actual - url ==> {url}{query_params}")
        return redirect(f'{url}{query_params}')                
    except Exception as error:
        print("Error editing call: ",error)
        return redirect('/')


"""
    Function to end an ongoing Call
"""    
def end_call(request):
    # print("Inside end call")
    try:
        # Extract the id from the POST request
        request_body = json.loads(request.body)
        call_id = request_body['call_id']
        campaign_id = request_body['campaign_id'] 
        
        # Fetch the CallLog record with the given id
        call_history_record = CallLogs.objects(campaign_id=int(campaign_id), call_id= call_id).first()

        if call_history_record:
            call_id = call_history_record.call_id
            # print("Found call history record with call_id:", call_id)
            
            # Make the external API request with the fetched call_id
            api_url = f"{settings.CALL_SERVER_BASE_URL}/end_call"
            
            payload = {"call_id": call_id}
            headers = {
                # 'Authorization': 'Bearer a9e11af5ec4c6491dbd82e8a6f3dfde3'
                 'Content-Type': 'application/json'
            }
            
            response = requests.post(api_url, headers=headers, json=payload)
            response = response.json()
            print("External API response:", response)
            
            ## Update the status in the database
            if ('success' in response and response['success'] ) or ("error" in response and response['error'] and response['error_message']=="Call is already finished or not started" ):
                call_history_record.update(set__call_status="completed")

            # Return the response from the external API
            return JsonResponse({"error": False, "success":True, "message":"Successfully ended the call."}, status=200)
        else:
            print("No call history record found for id:", call_id)
            return JsonResponse({"error": True, "success":False, "message":"No call history record found for call"}, status=404)

    except Exception as err:
        print("error in end_call: ", err)
        return JsonResponse({"error": True, "success":False, "message":"Error Ending the call"}, status=500)
        
############################################################################################################################################################ 
######################################################## Live transcript of the Call #######################################################################
def live_call_list(request):
    try:
        if request.method == "GET":
            try:
                campaign_list = Campaign.objects.filter(is_delete=False)
                if not request.user.is_superuser:
                    campaign_list = campaign_list.filter(organisation_name=request.user.organisation_name)

                campaign_list = list(campaign_list.values("id", "campaign_name"))

                campaign_id = request.GET.get('campaign_id',0)
                call_status = "ongoing"
                call_logs_data = []
                dynamic_columns = []
                total_pages = 0
                page = 1
                paginated_logs =[]
                if campaign_id:
                    call_logs = CallLogs.objects(campaign_id=int(campaign_id)).order_by('-created_at')
                    if call_status:
                        call_logs = call_logs.filter(call_status="ongoing")

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
                    "breadcrumb": {"title": "View Live Calls", "parent": "Pages", "child": "Live Monitoring"},
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

                return render(request, 'pages/campaign/live_calls.html', context)
                
            except Exception as error:
                print("live_call_list get: ",error)
                return JsonResponse({"error": "No call logs found for this campaign"}, status=404)
    except Exception as error:
        print("Error editing call: ",error)
        return redirect('/')
            
def live_transcript(request):
    if request.method=="GET":
        campaign_id = request.GET.get('campaign_id')
        call_id = request.GET.get('call_id')
        
        transcript_server_url = settings.TRANSCRIPT_SERVER_URL # URL of live transcript

        campaign_name = Campaign.objects.get(id=campaign_id).campaign_name
        context = {"campaign_name":campaign_name,"call_id":call_id,"transcript_server_url":transcript_server_url}
        return render(request, 'pages/campaign/live_transcript.html', context)


############################################################################################################################################################

###################################################### Schedule Campaign Start #######################################################################
def schedule_campaign(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            campaign_id = data.get('campaign_id')
            schedule_note = data.get('schedule_note')
            schedule_date = data.get('schedule_date')

            # Assuming you have a campaign model to validate campaign_id

            campaign_obj = Campaign.objects.get(id=campaign_id)
            if not campaign_obj.is_schedule:
                ScheduleCampaign.objects.create(
                    campaign_id=campaign_id,
                    schedule_note=schedule_note,
                    schedule_date=schedule_date
                )

                # update the campaign is_scheduled to true
                campaign_obj.is_schedule = True
                campaign_obj.save()

                return JsonResponse({'message': 'Campaign scheduled successfully'}, status=200)
            else:
                return JsonResponse({'message': 'Unable to schedule the Campaign as it is already sheduled'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
################################################################### END ################################################################################
