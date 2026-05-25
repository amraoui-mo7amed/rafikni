from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from user_auth.models import UserProfile
from smtplib import SMTPException

from ..decorators import admin_required
from ..utils import (
    EmailConfigurationError,
    generate_secure_password,
    send_doctor_credentials_email,
    notify_admins,
)

import logging

logger = logging.getLogger(__name__)


@login_required
@admin_required
def user_list(request):
    query = request.GET.get("q", "")
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")  # active, inactive, banned (is_active=False)
    page = request.GET.get("page", 1)

    users = User.objects.select_related("profile").exclude(is_superuser=True)

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

    # Pagination
    paginator = Paginator(users, 10)  # 10 items per page
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    context = {
        "users": users_page,
        "query": query,
        "role": role,
        "status": status,
        "role_choices": UserProfile.RoleChoices.choices,
        "status_choices": [("active", "نشط"), ("inactive", "محظور / غير نشط")],
        "paginator": paginator,
    }
    return render(request, "dashboard/users/user_list.html", context)


@login_required
@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        data = {
            "username": user.username,
            "email": user.email[:21],
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


@login_required
def profile_update(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        birthdate = request.POST.get("birthdate")
        profile_pic = request.FILES.get("profile_pic")

        errors = []

        # Validation
        if not email:
            errors.append("البريد الإلكتروني مطلوب")
        elif User.objects.filter(email=email).exclude(pk=user.pk).exists():
            errors.append("هذا البريد الإلكتروني مستخدم بالفعل")

        if not errors:
            try:
                with transaction.atomic():
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.save()

                    profile.phone_number = phone_number
                    if birthdate:
                        profile.birthdate = birthdate
                    if profile_pic:
                        profile.profile_pic = profile_pic
                    profile.save()

                return JsonResponse(
                    {"success": True, "message": "تم تحديث الملف الشخصي بنجاح"}
                )
            except Exception as e:
                return JsonResponse({"success": False, "errors": [str(e)]})

        return JsonResponse({"success": False, "errors": errors})

    context = {
        "profile": profile,
    }
    return render(request, "dashboard/profile_update.html", context)


@login_required
@admin_required
def doctor_create(request):
    """
    View to create a new doctor account with auto-generated password
    """
    if request.method == "POST":
        # Get form data
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone_number = request.POST.get("phone_number")
        birthdate = request.POST.get("birthdate")
        profile_pic = request.FILES.get("profile_pic")

        errors = []

        # Validation
        if not all([username, email]):
            errors.append("يرجى ملء جميع الحقول المطلوبة")

        if User.objects.filter(username=username).exists():
            errors.append("اسم المستخدم موجود بالفعل")

        if User.objects.filter(email=email).exists():
            errors.append("البريد الإلكتروني مستخدم بالفعل")

        if not errors:
            try:
                # Generate secure password
                password = generate_secure_password()

                with transaction.atomic():
                    # Create user with is_active=True (doctors are active by default)
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name or "",
                        last_name=last_name or "",
                        is_active=True,
                    )

                    # Update doctor profile (signal might have already created it)
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    profile.role = UserProfile.RoleChoices.DOC
                    profile.phone_number = phone_number or ""
                    if birthdate:
                        profile.birthdate = birthdate
                    profile.save()

                    # Handle profile picture if uploaded
                    if profile_pic:
                        profile.profile_pic = profile_pic
                        profile.save()

                    # Send credentials email before committing transaction
                    # If email fails, transaction will rollback
                    send_doctor_credentials_email(request, user, password)

                # Notify other admins
                notify_admins(
                    title="حساب طبيب جديد",
                    message=f"تم إنشاء حساب جديد للطبيب {username} بواسطة {request.user.username}",
                    notification_type="success",
                    link=reverse("dashboard:user_list") + f"?q={username}",
                )

                logger.info(
                    f"Doctor account created and email sent: {username} by {request.user.username}"
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"تم إنشاء حساب الطبيب {username} بنجاح. تم إرسال بيانات الدخول إلى {email}",
                    }
                )

            except EmailConfigurationError as e:
                logger.error(f"Email configuration error: {str(e)}")
                errors.append(str(e))
            except SMTPException as e:
                logger.error(f"SMTP error: {str(e)}")
                errors.append(f"فشل إرسال البريد الإلكتروني: {str(e)}")
            except Exception as e:
                logger.error(f"Error creating doctor account: {str(e)}")
                errors.append("حدث خطأ أثناء إنشاء الحساب")

        return JsonResponse({"success": False, "errors": errors})

    # GET request - render the form
    return render(request, "dashboard/users/doctor_create.html")
