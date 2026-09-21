"""
Authentication backends for Rafikni platform.
Allows users to authenticate with either their username or their email address.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that supports authentication using either
    the username or the email address with case-insensitive matching.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user via username or email.
        """
        if username is None:
            username = kwargs.get("email")

        if username is None or password is None:
            return None

        # Look up user by username or email (case-insensitive)
        user = User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
