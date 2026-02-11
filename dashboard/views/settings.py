from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import get_connection
from django.core.mail.backends.smtp import EmailBackend
from ..models import EmailConfiguration
from ..decorators import admin_required


@admin_required
def test_email_connection(request):
    if request.method == "POST":
        email_host = request.POST.get("email_host")
        email_port = request.POST.get("email_port")
        email_host_user = request.POST.get("email_host_user")
        email_host_password = request.POST.get("email_host_password")
        email_use_tls = request.POST.get("email_use_tls") == "on"
        email_use_ssl = request.POST.get("email_use_ssl") == "on"

        try:
            backend = EmailBackend(
                host=email_host,
                port=int(email_port) if email_port else 587,
                username=email_host_user,
                password=email_host_password,
                use_tls=email_use_tls,
                use_ssl=email_use_ssl,
                timeout=10,
            )
            connection = backend.open()
            if connection:
                backend.close()
                return JsonResponse({"success": True, "message": "تم الاتصال بنجاح"})
            else:
                return JsonResponse(
                    {"success": False, "errors": ["فشل الاتصال بخادم البريد"]}
                )
        except Exception as e:
            return JsonResponse(
                {"success": False, "errors": [f"خطأ في الاتصال: {str(e)}"]}
            )

    return JsonResponse({"success": False, "errors": ["طلب غير صالح"]})


@admin_required
def email_settings(request):
    config = EmailConfiguration.objects.first()

    if request.method == "POST":
        name = request.POST.get("name")
        email_host = request.POST.get("email_host")
        email_port = request.POST.get("email_port")
        email_host_user = request.POST.get("email_host_user")
        email_host_password = request.POST.get("email_host_password")
        email_use_tls = request.POST.get("email_use_tls") == "on"
        email_use_ssl = request.POST.get("email_use_ssl") == "on"
        default_from_email = request.POST.get("default_from_email")
        is_active = request.POST.get("is_active") == "on"

        errors = []
        if not all(
            [
                name,
                email_host,
                email_port,
                email_host_user,
                email_host_password,
                default_from_email,
            ]
        ):
            errors.append("يرجى ملء جميع الحقول المطلوبة")

        if not errors:
            try:
                if not config:
                    config = EmailConfiguration()

                config.name = name
                config.email_host = email_host
                config.email_port = int(email_port) if email_port else 587
                config.email_host_user = email_host_user
                config.email_host_password = email_host_password
                config.email_use_tls = email_use_tls
                config.email_use_ssl = email_use_ssl
                config.default_from_email = default_from_email
                config.is_active = is_active
                config.save()

                return JsonResponse({"success": True, "message": "تم حفظ الإعدادات بنجاح"})
            except Exception as e:
                errors.append(f"حدث خطأ أثناء الحفظ: {str(e)}")

        return JsonResponse({"success": False, "errors": errors})

    return render(request, "settings/email_settings.html", {"config": config})
