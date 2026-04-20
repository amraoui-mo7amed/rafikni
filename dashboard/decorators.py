from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from user_auth.models import UserProfile


def admin_required(view_func):
    """
    Decorator for views that checks if the user is an admin.
    """

    def is_admin(user):
        return user.is_authenticated and (
            user.is_superuser
            or (hasattr(user, "profile") and user.profile.role == UserProfile.RoleChoices.ADMIN)
        )

    actual_decorator = user_passes_test(
        is_admin, login_url="user_auth:login", redirect_field_name=None
    )

    return actual_decorator(view_func)


def patient_required(view_func):
    """
    Decorator for views that checks if the user is a patient.
    """

    def is_patient(user):
        return user.is_authenticated and (
            hasattr(user, "profile")
            and user.profile.role == UserProfile.RoleChoices.PATIENT
        )

    actual_decorator = user_passes_test(
        is_patient, login_url="user_auth:login", redirect_field_name=None
    )

    return actual_decorator(view_func)


def patient_or_admin_required(view_func):
    """
    Decorator for views that checks if the user is either a patient or an admin.
    """

    def is_patient_or_admin(user):
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if hasattr(user, "profile"):
            return user.profile.role in [UserProfile.RoleChoices.PATIENT, "admin"]
        return False

    actual_decorator = user_passes_test(
        is_patient_or_admin, login_url="user_auth:login", redirect_field_name=None
    )

    return actual_decorator(view_func)
