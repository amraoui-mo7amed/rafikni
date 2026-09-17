"""
User & Doctor Management Router for Rafikni Platform.
Administrative endpoints for managing accounts, banning/activating users, and onboarding certified specialists.
"""

from typing import Optional
from ninja import Router, Form, File, UploadedFile
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from user_auth.models import UserProfile
from dashboard.utils import (
    generate_secure_password,
    send_doctor_credentials_email,
    notify_admins,
    EmailConfigurationError,
)
from api.security import AdminAuth
from api.utils import api_response
from api.serializers import serialize_user_profile
from api.schemas.common import ApiResponseSchema
from api.schemas.users import (
    UserListItemSchema,
    PaginatedUsersSchema,
)

router = Router()


@router.get("/", auth=AdminAuth(), response=ApiResponseSchema[PaginatedUsersSchema])
def list_users(
    request,
    q: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
):
    """
    Admin: List platform users with filters for search, role, and active status.
    """
    users = User.objects.select_related("profile").exclude(is_superuser=True).order_by("-date_joined")

    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )

    if role and role in UserProfile.RoleChoices.values:
        users = users.filter(profile__role=role)

    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 15)
    try:
        users_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        users_page = paginator.page(1)

    items = [serialize_user_profile(u, request) for u in users_page]

    pagination_data = {
        "page": users_page.number,
        "num_pages": paginator.num_pages,
        "total_count": paginator.count,
        "has_next": users_page.has_next(),
        "has_prev": users_page.has_previous(),
    }

    return api_response(
        success=True,
        message="تم جلب المستخدمين بنجاح",
        data={"items": items, "pagination": pagination_data},
        status=200,
    )


@router.get("/{user_id}", auth=AdminAuth(), response={200: ApiResponseSchema[UserListItemSchema], 404: ApiResponseSchema[None]})
def get_user_detail(request, user_id: int):
    """
    Admin: Retrieve complete profile and activity records for a specific user.
    """
    try:
        user = User.objects.select_related("profile").get(id=user_id)
        data = serialize_user_profile(user, request)
        return api_response(success=True, message="تم جلب تفاصيل المستخدم بنجاح", data=data, status=200)
    except User.DoesNotExist:
        return api_response(success=False, message="المستخدم غير موجود", errors=["المستخدم غير موجود"], status=404)


@router.post("/{user_id}/toggle-status", auth=AdminAuth(), response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def toggle_user_status(request, user_id: int):
    """
    Admin: Toggle a user's active/banned status. Superusers are protected from being banned.
    """
    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            return api_response(success=False, message="لا يمكن حظر المدير العام", errors=["لا يمكن حظر المدير العام"], status=400)

        user.is_active = not user.is_active
        user.save()
        status_text = "تفعيل" if user.is_active else "حظر"
        return api_response(success=True, message=f"تم {status_text} المستخدم بنجاح", status=200)
    except User.DoesNotExist:
        return api_response(success=False, message="المستخدم غير موجود", errors=["المستخدم غير موجود"], status=404)


@router.delete("/{user_id}", auth=AdminAuth(), response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def delete_user(request, user_id: int):
    """
    Admin: Permanently delete a user account and profile. Superusers are protected from deletion.
    """
    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            return api_response(success=False, message="لا يمكن حذف المدير العام", errors=["لا يمكن حذف المدير العام"], status=400)

        user.delete()
        return api_response(success=True, message="تم حذف المستخدم بنجاح", status=200)
    except User.DoesNotExist:
        return api_response(success=False, message="المستخدم غير موجود", errors=["المستخدم غير موجود"], status=404)


@router.post("/create-doctor", auth=AdminAuth(), response={201: ApiResponseSchema[UserListItemSchema], 400: ApiResponseSchema[None]})
def create_doctor_account(
    request,
    username: str = Form(...),
    email: str = Form(...),
    first_name: Optional[str] = Form(""),
    last_name: Optional[str] = Form(""),
    phone_number: Optional[str] = Form(""),
    birthdate: Optional[str] = Form(""),
    profile_pic: Optional[UploadedFile] = File(None),
):
    """
    Admin: Create a new doctor/specialist account with an auto-generated secure password.
    Dispatches credentials email in an atomic transaction; rolls back if email delivery fails.
    """
    if not all([username, email]):
        return api_response(success=False, message="يرجى ملء جميع الحقول المطلوبة", errors=["يرجى ملء جميع الحقول المطلوبة"], status=400)

    if User.objects.filter(username=username).exists():
        return api_response(success=False, message="اسم المستخدم موجود بالفعل", errors=["اسم المستخدم موجود بالفعل"], status=400)

    if User.objects.filter(email=email).exists():
        return api_response(success=False, message="البريد الإلكتروني مستخدم بالفعل", errors=["البريد الإلكتروني مستخدم بالفعل"], status=400)

    try:
        password = generate_secure_password()

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name or "",
                last_name=last_name or "",
                is_active=True,
            )

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = UserProfile.RoleChoices.DOC
            profile.phone_number = phone_number or ""
            if birthdate:
                profile.birthdate = birthdate
            if profile_pic:
                profile.profile_pic = profile_pic
            profile.save()

            # Atomic email dispatch - rolls back transaction if email fails
            send_doctor_credentials_email(request, user, password)

        notify_admins(
            title="حساب طبيب جديد",
            message=f"تم إنشاء حساب جديد للطبيب {username} بواسطة {request.user.username}",
            notification_type="success",
            link=reverse("dashboard:user_list") + f"?q={username}",
        )

        user_data = serialize_user_profile(user, request)
        return api_response(
            success=True,
            message=f"تم إنشاء حساب الطبيب {username} بنجاح وإرسال بيانات الدخول إلى {email}",
            data=user_data,
            status=201,
        )

    except EmailConfigurationError as e:
        return api_response(success=False, message=f"فشل إرسال بيانات الدخول: {str(e)}", errors=[str(e)], status=400)
    except Exception as e:
        return api_response(success=False, message="حدث خطأ أثناء إنشاء الحساب", errors=[str(e)], status=400)
