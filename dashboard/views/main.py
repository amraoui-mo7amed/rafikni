from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse


# @login_required
def index(request):
    return render(request, "dashboard/dash_index.html")
