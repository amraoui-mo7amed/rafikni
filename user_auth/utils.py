"""
Authentication and user account utility functions for Rafikni.
"""

import uuid
from django.contrib.auth.models import User


def generate_unique_username(prefix: str = "user_") -> str:
    """
    Generate a unique username formatted as `user_<uuid>`.

    Uses uuid4 to generate a random 12-character hex suffix and verifies
    uniqueness against existing User records in the database.

    Args:
        prefix (str): Prefix string for the username, defaults to 'user_'.

    Returns:
        str: A unique username string conforming to Django's username constraints (e.g., 'user_a1b2c3d4e5f6').
    """
    while True:
        unique_suffix = uuid.uuid4().hex[:12]
        candidate = f"{prefix}{unique_suffix}"
        if not User.objects.filter(username=candidate).exists():
            return candidate
