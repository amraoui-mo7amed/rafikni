"""
Authentication & User Profile Router for Rafikni Platform.
Endpoints for registration, login, token refresh, password reset, and profile management.
"""

from typing import Optional
from ninja import Router, Form, File, UploadedFile
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse

from user_auth.models import UserProfile
from user_auth.utils import generate_unique_username
from user_auth.views.auth import send_styled_email
from api.jwt_auth import generate_tokens_for_user, get_user_from_token
from api.security import JWTAuth
from api.utils import api_response
from api.serializers import serialize_user_profile
from api.schemas.common import ApiResponseSchema
from api.schemas.auth import (
    SignupSchema,
    LoginSchema,
    RefreshTokenSchema,
    ActivateSchema,
    LostPasswordSchema,
    PasswordResetConfirmSchema,
    TokenResponseSchema,
    UserProfileOutSchema,
)

router = Router()


@router.post("/signup", response={201: ApiResponseSchema[None], 400: ApiResponseSchema[None]})
def signup(request, data: SignupSchema):
    """
    Register a new patient account and send an email verification link.
    Generates a unique username formatted like user_<uuid> if not explicitly specified.
    """
    errors = []
    if not all([data.email, data.password, data.confirm_password]):
        errors.append("يرجى ملء جميع الحقول المطلوبة")
    elif data.password != data.confirm_password:
        errors.append("كلمات المرور غير متطابقة")
    elif User.objects.filter(email=data.email).exists():
        errors.append("البريد الإلكتروني مستخدم بالفعل")

    username = data.username.strip() if (data.username and data.username.strip()) else None
    if username:
        if User.objects.filter(username=username).exists():
            errors.append("اسم المستخدم موجود بالفعل")
    else:
        username = generate_unique_username()

    if errors:
        return api_response(success=False, message="بيانات التسجيل غير صالحة", errors=errors, status=400)

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=data.email,
                password=data.password,
                is_active=False,
            )
            UserProfile.objects.get_or_create(
                user=user, defaults={"role": UserProfile.RoleChoices.PATIENT}
            )

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activation_url = request.build_absolute_uri(
                reverse("user_auth:activate", kwargs={"uidb64": uid, "token": token})
            )

            sent = send_styled_email(
                request,
                user,
                "تفعيل حسابك في رافقني",
                "emails/email_verification.html",
                {"activation_url": activation_url},
            )
            if not sent:
                raise RuntimeError("فشل في إرسال بريد التفعيل الإلكتروني")

        return api_response(
            success=True,
            message="تم إنشاء الحساب بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل الحساب.",
            status=201,
        )
    except Exception as e:
        return api_response(success=False, message="حدث خطأ أثناء إنشاء الحساب أو إرسال بريد التفعيل", errors=[str(e)], status=400)


@router.post("/login", response={200: ApiResponseSchema[TokenResponseSchema], 401: ApiResponseSchema[None]})
def login(request, data: LoginSchema):
    """
    Authenticate with username or email and password, returning JWT access and refresh tokens.
    """
    username_or_email = data.username.strip()
    user = authenticate(request, username=username_or_email, password=data.password)

    if user is None:
        existing_user = User.objects.filter(
            Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
        ).first()
        if existing_user and existing_user.check_password(data.password) and not existing_user.is_active:
            return api_response(
                success=False,
                message="يرجى تفعيل حسابك من خلال البريد الإلكتروني أولاً",
                errors=["يرجى تفعيل حسابك من خلال البريد الإلكتروني أولاً"],
                status=401,
            )
        return api_response(
            success=False,
            message="اسم المستخدم أو كلمة المرور غير صحيحة",
            errors=["اسم المستخدم أو كلمة المرور غير صحيحة"],
            status=401,
        )

    tokens = generate_tokens_for_user(user)
    user_data = serialize_user_profile(user, request)

    return api_response(
        success=True,
        message="تم تسجيل الدخول بنجاح",
        data={
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": user_data,
        },
        status=200,
    )


@router.post("/token/refresh", response={200: ApiResponseSchema[dict], 401: ApiResponseSchema[None]})
def refresh_token(request, data: RefreshTokenSchema):
    """
    Obtain a new 60-minute JWT access token using a valid 30-day refresh token.
    """
    user = get_user_from_token(data.refresh_token, expected_type="refresh")
    if not user:
        return api_response(
            success=False,
            message="رمز التحديث غير صالح أو منتهي الصلاحية",
            errors=["رمز التحديث غير صالح أو منتهي الصلاحية"],
            status=401,
        )

    tokens = generate_tokens_for_user(user)
    return api_response(
        success=True,
        message="تم تجديد رمز الدخول بنجاح",
        data={"access_token": tokens["access_token"]},
        status=200,
    )


@router.post("/activate", response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None]})
def activate_account(request, data: ActivateSchema):
    """
    Activate a user account via base64 encoded user ID and verification token.
    """
    try:
        uid = force_str(urlsafe_base64_decode(data.uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, data.token):
        user.is_active = True
        user.save()
        return api_response(success=True, message="تم تفعيل حسابك بنجاح. يمكنك الآن تسجيل الدخول.", status=200)

    return api_response(
        success=False,
        message="رابط التفعيل غير صالح أو منتهي الصلاحية",
        errors=["رابط التفعيل غير صالح أو منتهي الصلاحية"],
        status=400,
    )


@router.post("/lost-password", response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None]})
def lost_password(request, data: LostPasswordSchema):
    """
    Initiate a password reset by sending a recovery link to the user's email.
    """
    try:
        user = User.objects.get(email=data.email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = request.build_absolute_uri(
            reverse("user_auth:password_reset_confirm", kwargs={"uidb64": uid, "token": token})
        )
        send_styled_email(
            request,
            user,
            "إعادة تعيين كلمة المرور - رافقني",
            "emails/password_reset.html",
            {"reset_url": reset_url},
        )
        return api_response(success=True, message="تم إرسال رابط تعيين كلمة المرور إلى بريدك الإلكتروني", status=200)
    except User.DoesNotExist:
        return api_response(
            success=False, message="البريد الإلكتروني غير موجود", errors=["البريد الإلكتروني غير موجود"], status=400
        )
    except Exception as e:
        return api_response(success=False, message="حدث خطأ أثناء معالجة الطلب", errors=[str(e)], status=400)


@router.post("/password-reset-confirm", response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None]})
def password_reset_confirm(request, data: PasswordResetConfirmSchema):
    """
    Confirm and set a new password using verification tokens.
    """
    if data.password != data.confirm_password:
        return api_response(
            success=False, message="كلمات المرور غير متطابقة", errors=["كلمات المرور غير متطابقة"], status=400
        )

    try:
        uid = force_str(urlsafe_base64_decode(data.uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, data.token):
        user.set_password(data.password)
        user.save()
        return api_response(success=True, message="تم تغيير كلمة المرور بنجاح", status=200)

    return api_response(
        success=False,
        message="رابط إعادة التعيين غير صالح أو منتهي الصلاحية",
        errors=["رابط إعادة التعيين غير صالح أو منتهي الصلاحية"],
        status=400,
    )


@router.get("/me", auth=JWTAuth(), response=ApiResponseSchema[UserProfileOutSchema])
def get_current_user_profile(request):
    """
    Retrieve the profile details of the currently authenticated user.
    """
    data = serialize_user_profile(request.user, request)
    return api_response(success=True, message="تم جلب البيانات بنجاح", data=data, status=200)


@router.put("/me", auth=JWTAuth(), response={200: ApiResponseSchema[UserProfileOutSchema], 400: ApiResponseSchema[None]})
def update_current_user_profile(
    request,
    first_name: str = Form(""),
    last_name: str = Form(""),
    email: str = Form(""),
    phone_number: str = Form(""),
    birthdate: str = Form(""),
    profile_pic: Optional[UploadedFile] = File(None),
):
    """
    Update profile details (names, email, phone, birthdate, profile avatar) for the authenticated user.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if not email:
        return api_response(success=False, message="البريد الإلكتروني مطلوب", errors=["البريد الإلكتروني مطلوب"], status=400)

    if User.objects.filter(email=email).exclude(pk=user.pk).exists():
        return api_response(
            success=False,
            message="هذا البريد الإلكتروني مستخدم بالفعل",
            errors=["هذا البريد الإلكتروني مستخدم بالفعل"],
            status=400,
        )

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

        updated_data = serialize_user_profile(user, request)
        return api_response(success=True, message="تم تحديث الملف الشخصي بنجاح", data=updated_data, status=200)
    except Exception as e:
        return api_response(success=False, message="حدث خطأ أثناء تحديث الملف الشخصي", errors=[str(e)], status=400)
