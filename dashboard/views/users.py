from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from user_auth.models import UserProfile
from ..decorators import admin_required


@login_required
@admin_required
def user_list(request):
    query = request.GET.get("q", "")
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")  # active, inactive, banned (is_active=False)

    users = User.objects.select_related("profile").all()

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

    if role:
        users = users.filter(profile__role=role)

    if status:
        if status == "active":
            users = users.filter(is_active=True)
        elif status == "inactive":
            users = users.filter(is_active=False)

    context = {
        "users": users,
        "query": query,
        "role": role,
        "status": status,
        "role_choices": UserProfile.RoleChoices.choices,
        "status_choices": [("active", "نشط"), ("inactive", "محظور / غير نشط")],
    }
    return render(request, "dashboard/users/user_list.html", context)


@login_required
@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        data = {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.strftime("%Y-%m-%d"),
            "last_login": user.last_login.strftime("%Y-%m-%d %H:%M")
            if user.last_login
            else "لم يسجل دخول بعد",
            "is_active": user.is_active,
            "role": user.profile.get_role_display()
            if hasattr(user, "profile")
            else "غير محدد",
            "phone": user.profile.phone_number
            if hasattr(user, "profile")
            else "غير متوفر",
            "birthdate": user.profile.birthdate.strftime("%Y-%m-%d")
            if hasattr(user, "profile") and user.profile.birthdate
            else "غير متوفر",
        }
        return JsonResponse({"success": True, "data": data})
    return redirect("dashboard:user_list")


@login_required
@admin_required
def user_delete(request, pk):
    if request.method == "POST":
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            return JsonResponse(
                {"success": False, "message": "لا يمكن حذف المدير العام"}
            )
        user.delete()
        return JsonResponse({"success": True, "message": "تم حذف المستخدم بنجاح"})
    return JsonResponse({"success": False, "message": "طلب غير صالح"})


@login_required
@admin_required
def user_toggle_status(request, pk):
    if request.method == "POST":
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            return JsonResponse(
                {"success": False, "message": "لا يمكن حظر المدير العام"}
            )
        user.is_active = not user.is_active
        user.save()
        status_text = "تفعيل" if user.is_active else "حظر"
        return JsonResponse(
            {"success": True, "message": f"تم {status_text} المستخدم بنجاح"}
        )
    return JsonResponse({"success": False, "message": "طلب غير صالح"})
