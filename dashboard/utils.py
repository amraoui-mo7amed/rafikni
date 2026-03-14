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


def get_all_medical_cases():
    """
    Helper function to get all medical cases from all models with type info.

    This function queries all three medical case models (Child, Adult, Elderly)
    and adds additional attributes to each case for frontend display purposes.

    Returns:
        list: List of all medical cases with added attributes:
            - case_type: 'child', 'adult', or 'elderly'
            - case_type_display: Arabic display name
            - case_model: Django model class name

    Note:
        Results are sorted by ID descending (newer first)
    """
    from .models import ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase

    all_cases = []

    for c in ChildMedicalCase.objects.all():
        c.case_type = "child"
        c.case_type_display = "طفل"
        c.case_model = "ChildMedicalCase"
        all_cases.append(c)

    for c in AdultMedicalCase.objects.all():
        c.case_type = "adult"
        c.case_type_display = "بالغ"
        c.case_model = "AdultMedicalCase"
        all_cases.append(c)

    for c in ElderlyMedicalCase.objects.all():
        c.case_type = "elderly"
        c.case_type_display = "مسن"
        c.case_model = "ElderlyMedicalCase"
        all_cases.append(c)

    all_cases.sort(key=lambda x: x.id, reverse=True)
    return all_cases


def filter_cases_by_user(cases, user):
    """
    Filter medical cases based on user permissions.

    Admins (is_staff or is_superuser) can see all cases,
    while regular users can only see their own cases.

    Args:
        cases: List of medical case objects
        user: The User object to filter by

    Returns:
        list: Filtered list of cases based on user permissions

    Logic:
        - If user.is_staff or user.is_superuser: return all cases
        - Otherwise: return only cases where case.user == user
    """
    if user.is_staff or user.is_superuser:
        return cases
    return [c for c in cases if c.user == user]
