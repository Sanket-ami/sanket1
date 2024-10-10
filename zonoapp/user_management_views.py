from django.shortcuts import render,redirect
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate
from .models import  Notification , User, Role
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404

def list_of_user(request, user_id:int=None):
    if request.method == "GET":

        if request.user.is_superuser:
            user_list = User.objects.all()
            role_list = Role.objects.values('role','id').distinct('role')
            organisation_list = User.objects.values('organisation_name').distinct('organisation_name')
            return render(request,'pages/user_management/add_user.html', {'users': user_list, 'roles': role_list, 'organisation_list': organisation_list})
        
        if request.user.role.role == 'Admin':
            user_list = User.objects.all().filter(organisation_name=request.user.organisation_name)
            role_list = Role.objects.values('role').distinct()
            organisation_list = User.objects.values('organisation_name').filter(organisation_name=request.user.organisation_name).distinct()
            user_list = User.objects.all().filter(organisation_name=request.user.organisation_name)
            return render(request,'pages/user_management/add_user.html', {'users': user_list, 'roles': role_list, 'organisation_list': organisation_list})
        
    elif request.method == "POST":
        print("In post method")
        data = json.loads(request.body)
        print("data ====>", data)
        data['role'] = Role.objects.get(id=data['role'])
        try:
            user = User.objects.create(
                username= data['username'],
                first_name = data['first_name'],
                password=make_password(data['password']),
                email=data['email'],
                role=data['role'],
                organisation_name=data['organisation_name']
            )
            # Notify for new user creation
            notify = Notification.objects.create(user=user, message=f'New user {user.username} has been created.',organisation_name=data['organisation_name'])
            print(" notify  ",notify)
            return JsonResponse({'status': 'created', 'status_code':201})
        except Exception as e:
            return JsonResponse({'status': f'not created {e}', 'status_code':400})
    
    elif request.method == "DELETE":
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')  # Expecting 'user_id' in the request body
            print(data)
            user = get_object_or_404(User, id=user_id)
            organisation_name = user.organisation_name
            username = user.username
            print("user data : ",user.email , organisation_name)
            user.update(is_deleted = True)
            # Notify for delete user 
            Notification.objects.create(user=user ,message=f' user {username} has been deleted.',organisation_name=organisation_name)
            return JsonResponse({'status': 'User deleted successfully', 'status_code': 200}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'status': 'User not found', 'status_code': 404}, status=404)
        except Exception as e:
            return JsonResponse({'status': f'User deletion failed: {e}', 'status_code': 400}, status=400)
        
    elif request.method == "PUT":
       
        print("data=====>", request.body)
        data = json.loads(request.body)
        print(data)
        user_id = data['user_id']
        user_data = get_object_or_404(User, id=user_id)  # Using get_object_or_404 for better error handling

        # Assuming 'user' refers to the user making the request
        user = request.user  # Get the current authenticated user

        # Update user information
        user_data.email = data['email']
        user_data.role = Role.objects.get(id=data['role'])
        user_data.save()

        # Notify for updated user info
        print("User data :: ", user_data)
        username = user_data.username
        organisation_name = user_data.organisation_name 

        Notification.objects.create(user=user, message=f'User {username} has updated their info.', organisation_name=organisation_name)

        return JsonResponse({'status': 'User updated successfully', 'status_code': 200}, status=200)
    #     return JsonResponse({"status": "User not found", "status_code": 404}, status=404)
    # return JsonResponse({"status": "Method Not allowed"}, status=200)


def get_user(request, user_id:int):
    if request.method == 'GET':
        user_data = User.objects.get(id=user_id)
        print(user_data.role.role)
        user_data = {
            "username": user_data.email,
            "role": None if not user_data.role else user_data.role.role,
            "email": user_data.email
        }
        return JsonResponse(user_data)
    else:
        return JsonResponse({'error': 'Invalid HTTP method'}, status=405)
