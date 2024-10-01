from django.shortcuts import render,redirect
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate
from .models import User, Role
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
import json

def list_of_user(request):
    print(1234)
    if request.method == "GET":
        if request.user.is_superuser:
            user_list = User.objects.all()
            role_list = Role.objects.values('role','id').distinct('role')
            organisation_list = User.objects.values('organisation_name').distinct('organisation_name')
            return render(request,'pages/user_management/add_user.html', {'users': user_list, 'roles': role_list, 'organisation_list': organisation_list})
        if request.user.role == 'admin':
            user_list = User.objects.all().filter(oraganisation_name=request.user.organisation_name)
            role_list = Role.objects.values('role').filter(oraganisation_name=request.user.organisation_name).distinct()
            organisation_list = User.objects.values('organisation_name').filter(oraganisation_name=request.user.organisation_name).distinct()
        user_list = User.objects.all().filter(User.role.organisation_name==request.role.organisation_name)
        return JsonResponse({'status': 'created', 'status_code':201}, status=201)
        
    elif request.method == "POST":
        data = json.loads(request.body)
        print(data)
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
            return JsonResponse({'status': 'created', 'status_code':201})
        except Exception as e:
            return JsonResponse({'status': f'not created {e}', 'status_code':400})

        
