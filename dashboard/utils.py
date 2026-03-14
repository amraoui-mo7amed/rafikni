import logging
import secrets
import string
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from django_eventstream import send_event

from user_auth.models import UserProfile
from .models import Notification, Payment

logger = logging.getLogger(__name__)


class EmailConfigurationError(Exception):
    """Raised when email configuration is invalid or server doesn't support required features"""

    pass


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


def create_notification(user, title, message, notification_type="info", link=""):
    """
    Create a notification for a user and send it via eventstream.

    Args:
        user: The user to notify
        title: Notification title
        message: Notification message
        notification_type: One of 'info', 'success', 'warning', 'error'
        link: Optional link to navigate to when clicked

    Returns:
        The created Notification instance
    """
    try:
        # Create notification in database
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )

        # Send real-time event to user's channel
        channel = f"user-{user.id}"
        event_data = {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
            "link": notification.link,
        }

        send_event(channel, "notification", event_data)

        logger.info(f"Notification sent to user {user.username}: {title}")
        return notification

    except Exception as e:
        logger.error(
            f"Failed to create notification for user {user.username}: {str(e)}"
        )
        return None


def notify_user(user, title, message, notification_type="info", link=""):
    """
    Alias for create_notification - sends a notification to a user.
    """
    return create_notification(user, title, message, notification_type, link)


def notify_users(users, title, message, notification_type="info", link=""):
    """
    Send the same notification to multiple users.

    Args:
        users: QuerySet or list of users
        title: Notification title
        message: Notification message
        notification_type: One of 'info', 'success', 'warning', 'error'
        link: Optional link
    """
    notifications = []
    for user in users:
        notification = create_notification(
            user, title, message, notification_type, link
        )
        if notification:
            notifications.append(notification)

    return notifications


def notify_admins(request, title, message, notification_type="info", link=""):
    """
    Send notification to all admin users.
    """
    admin_users = User.objects.filter(
        profile__role=UserProfile.RoleChoices.ADMIN, is_active=True
    )

    return notify_users(admin_users, title, message, notification_type, link)


def create_payment(user, content_object, receipt_image):
    """
    Create a payment object for a user.

    Args:
        user: The user making the payment
        content_object: The object being paid for (e.g., CourseEnrollment, MedicalCase)
        receipt_image: The receipt image file

    Returns:
        The created Payment instance
    """
    content_type = ContentType.objects.get_for_model(content_object)

    payment = Payment.objects.create(
        user=user,
        content_type=content_type,
        object_id=content_object.id,
        content_object=content_object,
        receipt_image=receipt_image,
        status=Payment.PaymentStatus.PENDING,
    )

    logger.info(f"Payment created: {payment.id} for user {user.username}")
    return payment
