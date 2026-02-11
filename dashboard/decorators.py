from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorator for views that checks if the user is an admin.
    """

    def is_admin(user):
        return user.is_authenticated and (
            user.is_superuser
            or (hasattr(user, "profile") and user.profile.role == "admin")
        )

    actual_decorator = user_passes_test(
        is_admin, login_url="user_auth:login", redirect_field_name=None
    )

    return actual_decorator(view_func)
