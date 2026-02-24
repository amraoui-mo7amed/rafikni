from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.urls import reverse
from ..models import UserProfile
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from dashboard.models import EmailConfiguration
import logging

logger = logging.getLogger(__name__)


def send_styled_email(request, user, subject, template_name, context_extra):
    """
    وظيفة مساعدة لإرسال رسائل بريد إلكتروني منسقة.
    """
    current_site = get_current_site(request)
    context = {
        "user": user,
        "domain": current_site.domain,
        "protocol": "https" if request.is_secure() else "http",
        **context_extra,
    }
    message = render_to_string(template_name, context)

    # Get the configured sender email
    from_email = None
    try:
        email_config = EmailConfiguration.objects.filter(is_active=True).first()
        if email_config:
            from_email = email_config.default_from_email
            logger.info(f"Using configured from_email: {from_email}")
    except Exception as e:
        logger.warning(f"Could not load email configuration: {str(e)}")

    email = EmailMessage(subject, message, from_email=from_email, to=[user.email])
    email.content_subtype = "html"

    try:
        result = email.send(fail_silently=False)
        logger.info(f"Email sent successfully to {user.email}")
        return result
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        raise


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        errors = []
        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_active:
                    errors.append("يرجى تفعيل حسابك من خلال البريد الإلكتروني أولاً")
                    return JsonResponse({"success": False, "errors": errors})

                login(request, user)
                return JsonResponse(
                    {
                        "success": True,
                        "message": "تم تسجيل الدخول بنجاح",
                        "redirect_url": reverse("dashboard:index"),
                    }
                )
            else:
                errors.append("اسم المستخدم أو كلمة المرور غير صحيحة")
                return JsonResponse({"success": False, "errors": errors})
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            errors.append("حدث خطأ أثناء تسجيل الدخول")
            return JsonResponse({"success": False, "errors": errors})

    return render(request, "auth.html", {"mode": "login"})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        errors = []

        if not all([username, email, password, confirm_password]):
            errors.append("يرجى ملء جميع الحقول")
        elif password != confirm_password:
            errors.append("كلمات المرور غير متطابقة")
        elif User.objects.filter(username=username).exists():
            errors.append("اسم المستخدم موجود بالفعل")
        elif User.objects.filter(email=email).exists():
            errors.append("البريد الإلكتروني مستخدم بالفعل")

        if not errors:
            try:
                with transaction.atomic():
                    # إنشاء المستخدم غير نشط حتى يتم التفعيل
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        is_active=False,
                    )

                    # إنشاء الملف الشخصي الافتراضي
                    UserProfile.objects.get_or_create(
                        user=user, defaults={"role": UserProfile.RoleChoices.PATIENT}
                    )

                # توليد رابط التفعيل
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                activation_url = request.build_absolute_uri(
                    reverse(
                        "user_auth:activate", kwargs={"uidb64": uid, "token": token}
                    )
                )

                # إرسال البريد
                send_styled_email(
                    request,
                    user,
                    "تفعيل حسابك في رافقني",
                    "emails/email_verification.html",
                    {"activation_url": activation_url},
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": "تم إنشاء الحساب بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل الحساب.",
                    }
                )
            except IntegrityError:
                errors.append("حدث خطأ أثناء إنشاء الحساب")
            except Exception as e:
                logger.error(f"Signup error: {str(e)}")
                errors.append("حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.")

        return JsonResponse({"success": False, "errors": errors})

    return render(request, "auth.html", {"mode": "signup"})


def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, "activation_success.html")
    else:
        return render(
            request,
            "auth.html",
            {
                "mode": "login",
                "error_message": "رابط التفعيل غير صالح أو منتهي الصلاحية.",
            },
        )


def lost_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        errors = []

        if not email:
            errors.append("يرجى إدخال البريد الإلكتروني")
        else:
            try:
                user = User.objects.get(email=email)
                # توليد رابط إعادة التعيين
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    reverse(
                        "user_auth:password_reset_confirm",
                        kwargs={"uidb64": uid, "token": token},
                    )
                )

                # إرسال البريد
                send_styled_email(
                    request,
                    user,
                    "إعادة تعيين كلمة المرور - رافقني",
                    "emails/password_reset.html",
                    {"reset_url": reset_url},
                )

                return JsonResponse(
                    {
                        "success": True,
                        "message": "تم إرسال رابط تعيين كلمة المرور إلى بريدك الإلكتروني",
                    }
                )
            except User.DoesNotExist:
                errors.append("البريد الإلكتروني غير موجود")
            except Exception as e:
                logger.error(f"Password reset request error: {str(e)}")
                errors.append("حدث خطأ أثناء معالجة الطلب")

        return JsonResponse({"success": False, "errors": errors})

    return render(request, "auth.html", {"mode": "lost_password"})


def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            errors = []

            if not password or not confirm_password:
                errors.append("يرجى إدخال كلمة المرور الجديدة")
            elif password != confirm_password:
                errors.append("كلمات المرور غير متطابقة")

            if not errors:
                user.set_password(password)
                user.save()
                return JsonResponse(
                    {"success": True, "message": "تم تغيير كلمة المرور بنجاح", 'redirect_url': reverse('user_auth:login')}
                )
            return JsonResponse({"success": False, "errors": errors})

        return render(
            request,
            "auth.html",
            {"mode": "reset_password_confirm", "uid": uidb64, "token": token},
        )
    else:
        return render(
            request,
            "auth.html",
            {
                "mode": "login",
                "error_message": "رابط إعادة التعيين غير صالح أو منتهي الصلاحية.",
            },
        )


def logout_view(request):
    logout(request)
    return redirect("user_auth:login")
