from django.shortcuts import render
from dashboard.models import Course


def index(request):
    latest_courses = Course.objects.filter(is_active=True)[:6]
    return render(request, "index.html", {"latest_courses": latest_courses})
