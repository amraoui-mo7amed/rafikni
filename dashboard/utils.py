import logging
import secrets
import string
from smtplib import SMTPException

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for i in range(length))
    # Ensure password has at least one of each type
    if (
        any(c.islower() for c in password)
        and any(c.isupper() for c in password)
        and any(c.isdigit() for c in password)
    ):
        return password
    return generate_secure_password(length)  # Regenerate if criteria not met


class EmailConfigurationError(Exception):
    """Raised when email configuration is invalid or server doesn't support required features"""

    pass


def send_doctor_credentials_email(request, user, password):
    """
    Send an email to the doctor with their login credentials
    """
    current_site = get_current_site(request)
    login_url = request.build_absolute_uri("/auth/login/")

    context = {
        "user": user,
        "username": user.username,
        "password": password,
        "login_url": login_url,
        "domain": current_site.domain,
        "protocol": "https" if request.is_secure() else "http",
    }

    message = render_to_string("emails/doctor_credentials.html", context)

    # Get configured sender email
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    email = EmailMessage(
        subject="بيانات الدخول إلى منصة رافقني",
        body=message,
        from_email=from_email,
        to=[user.email],
    )
    email.content_subtype = "html"

    try:
        email.send(fail_silently=False)
    except SMTPException as e:
        error_msg = str(e).lower()
        if "auth" in error_msg or "authentication" in error_msg:
            logger.error(f"SMTP authentication error: {str(e)}")
            raise EmailConfigurationError(
                "خادم البريد لا يدعم المصادقة. يرجى التأكد من إعدادات EMAIL_HOST_USER و EMAIL_HOST_PASSWORD في ملف .env"
            )
        else:
            logger.error(f"SMTP error: {str(e)}")
            raise EmailConfigurationError(f"فشل إرسال البريد الإلكتروني: {str(e)}")
