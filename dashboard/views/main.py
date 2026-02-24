from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone


# @login_required
def index(request):
    # Get user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    # Users joined this month
    current_month = timezone.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    users_this_month = User.objects.filter(date_joined__gte=current_month).count()

    # Users joined last month for comparison
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    users_last_month = User.objects.filter(
        date_joined__gte=last_month, date_joined__lt=current_month
    ).count()

    # Calculate percentage change
    if users_last_month > 0:
        users_growth = ((users_this_month - users_last_month) / users_last_month) * 100
    else:
        users_growth = 100 if users_this_month > 0 else 0

    # Users by role
    from user_auth.models import UserProfile

    users_by_role = UserProfile.objects.values("role").annotate(count=Count("role"))

    context = {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "users_this_month": users_this_month,
        "users_growth": round(users_growth, 1),
        "users_by_role": users_by_role,
        "role_choices": UserProfile.RoleChoices.choices,
    }

    return render(request, "dashboard/dash_index.html", context)
