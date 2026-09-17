"""
JWT Authentication Utilities for Rafikni Platform.
Handles token creation, decoding, and user resolution.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Optional, Dict, Any

import jwt
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

JWT_SECRET = getattr(settings, "SECRET_KEY", "rafikni-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=60)
REFRESH_TOKEN_LIFETIME = timedelta(days=30)


def generate_tokens_for_user(user: User) -> Dict[str, str]:
    """
    Generate JWT access and refresh tokens for an authenticated user.

    Args:
        user: Django User instance with related profile.

    Returns:
        Dict containing access_token and refresh_token strings.
    """
    now = datetime.now(timezone.utc)
    role = getattr(user.profile, "role", "patient") if hasattr(user, "profile") else "patient"
    if user.is_superuser:
        role = "admin"

    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "role": role,
        "type": "access",
        "exp": now + ACCESS_TOKEN_LIFETIME,
        "iat": now,
    }

    refresh_payload = {
        "user_id": user.id,
        "type": "refresh",
        "exp": now + REFRESH_TOKEN_LIFETIME,
        "iat": now,
    }

    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token string.

    Args:
        token: Bearer JWT string.

    Returns:
        Dict payload if valid, None if expired or invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT: {e}")
        return None


def get_user_from_token(token: str, expected_type: str = "access") -> Optional[User]:
    """
    Extract and verify the active User from a token string.

    Args:
        token: JWT string.
        expected_type: 'access' or 'refresh'.

    Returns:
        Active User instance or None.
    """
    payload = decode_token(token)
    if not payload:
        return None

    if payload.get("type") != expected_type:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    try:
        user = User.objects.select_related("profile").get(id=user_id, is_active=True)
        return user
    except User.DoesNotExist:
        return None
