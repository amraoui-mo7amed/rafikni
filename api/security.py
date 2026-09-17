"""
Django Ninja Security Classes for Rafikni Platform.
Implements HttpBearer JWT authentication and RBAC authorization.
"""

from typing import Optional, Any
from ninja.security import HttpBearer
from ninja.errors import HttpError
from django.contrib.auth.models import User
from user_auth.models import UserProfile
from .jwt_auth import get_user_from_token


class JWTAuth(HttpBearer):
    """
    Standard JWT Bearer Authentication for any active authenticated user.
    Populates request.user upon successful authentication.
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        user = get_user_from_token(token, expected_type="access")
        if user:
            request.user = user
            return user
        return None


class AdminAuth(JWTAuth):
    """
    Ensures the user has an active Admin role or superuser privileges.
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        user = super().authenticate(request, token)
        if not user:
            return None

        if user.is_superuser:
            return user

        role = getattr(user.profile, "role", None) if hasattr(user, "profile") else None
        if role == UserProfile.RoleChoices.ADMIN:
            return user

        raise HttpError(403, "ليس لديك صلاحية مدير للوصول إلى هذا المورد")


class PatientAuth(JWTAuth):
    """
    Ensures the user is an active Patient / Family member.
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        user = super().authenticate(request, token)
        if not user:
            return None

        role = getattr(user.profile, "role", None) if hasattr(user, "profile") else None
        if role == UserProfile.RoleChoices.PATIENT:
            return user

        raise HttpError(403, "هذا الإجراء مخصص للمرضى فقط")


class DoctorAuth(JWTAuth):
    """
    Ensures the user is an active certified Doctor / Specialist.
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        user = super().authenticate(request, token)
        if not user:
            return None

        role = getattr(user.profile, "role", None) if hasattr(user, "profile") else None
        if role == UserProfile.RoleChoices.DOC:
            return user

        raise HttpError(403, "هذا الإجراء مخصص للأطباء والأخصائيين فقط")


class PatientOrAdminAuth(JWTAuth):
    """
    Allows either Patients or Administrators to perform operations.
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        user = super().authenticate(request, token)
        if not user:
            return None

        if user.is_superuser:
            return user

        role = getattr(user.profile, "role", None) if hasattr(user, "profile") else None
        if role in (UserProfile.RoleChoices.PATIENT, UserProfile.RoleChoices.ADMIN):
            return user

        raise HttpError(403, "ليس لديك صلاحية كافية لتنفيذ هذه العملية")


def admin_docs_required(view_func):
    """
    Decorator for API documentation endpoints (Redoc UI and OpenAPI schema).
    Permits access only to platform administrators:
    - Checks active Django session (user.is_superuser, is_staff, or profile role admin).
    - Checks Authorization: Bearer <JWT> header for admin role.
    If unauthorized:
    - HTML requests are redirected to user_auth:login.
    - JSON / API requests return 403 Forbidden.
    """
    from functools import wraps
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.http import JsonResponse

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = getattr(request, "user", None)

        is_admin = False
        if user and user.is_authenticated:
            if user.is_superuser or user.is_staff:
                is_admin = True
            elif hasattr(user, "profile") and user.profile.role == UserProfile.RoleChoices.ADMIN:
                is_admin = True

        if not is_admin:
            auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                jwt_user = get_user_from_token(token, expected_type="access")
                if jwt_user:
                    if jwt_user.is_superuser or jwt_user.is_staff:
                        is_admin = True
                        request.user = jwt_user
                    elif hasattr(jwt_user, "profile") and jwt_user.profile.role == UserProfile.RoleChoices.ADMIN:
                        is_admin = True
                        request.user = jwt_user

        if is_admin:
            return view_func(request, *args, **kwargs)

        accept_header = request.headers.get("Accept", "")
        if "text/html" in accept_header and not request.path.endswith(".json"):
            login_url = reverse("user_auth:login")
            return redirect(f"{login_url}?next={request.path}")

        return JsonResponse(
            {
                "success": False,
                "message": "غير مصرح - الوصول إلى وثائق الواجهة البرمجية مقتصر على المشرفين فقط",
                "errors": ["يجب تسجيل الدخول بحساب مدير للوصول إلى التوثيق."],
                "data": {},
            },
            status=403,
        )

    return _wrapped_view

