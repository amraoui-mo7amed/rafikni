"""
Main Django Ninja API configuration for Rafikni Platform.
Instantiates NinjaAPI, registers custom exception handlers, and mounts all domain routers.
"""

import logging
from ninja import NinjaAPI, Redoc
from ninja.errors import ValidationError, AuthenticationError, HttpError
from django.http import JsonResponse

from api.routers.auth import router as auth_router
from api.routers.medical_cases import router as cases_router
from api.routers.treatment_plans import router as plans_router
from api.routers.courses import router as courses_router
from api.routers.payments import router as payments_router
from api.routers.games import router as games_router
from api.routers.articles import router as articles_router
from api.routers.notifications import router as notifications_router
from api.routers.users import router as users_router
from api.routers.geo import router as geo_router
from api.routers.analytics import router as analytics_router
from api.security import admin_docs_required

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="Rafikni RESTful API",
    version="1.0.0",
    description="Official API for Rafikni Platform - Specialized Psych & Special Needs Care in Algeria",
    docs=Redoc(),
    docs_url="/docs",
    docs_decorator=admin_docs_required,
)


@api.exception_handler(AuthenticationError)
def on_auth_error(request, exc):
    """Ensure authentication failures return the unified response envelope with 401."""
    return JsonResponse(
        {
            "success": False,
            "message": "غير مصرح - يرجى تسجيل الدخول أولاً",
            "errors": ["رمز الدخول غير صالح، منتهي الصلاحية، أو مفقود."],
            "data": {},
        },
        status=401,
    )


@api.exception_handler(HttpError)
def on_http_error(request, exc):
    """Ensure HTTP errors (like 403 Forbidden) return the unified response envelope."""
    msg = exc.message or "ليس لديك الصلاحيات الكافية لتنفيذ هذا الإجراء"
    return JsonResponse(
        {
            "success": False,
            "message": msg,
            "errors": [msg],
            "data": {},
        },
        status=exc.status_code,
    )


@api.exception_handler(ValidationError)
def on_validation_error(request, exc):
    """Ensure validation errors return the unified response envelope with 422."""
    error_list = []
    for err in exc.errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "قيمة غير صالحة")
        error_list.append(f"{loc}: {msg}" if loc else msg)

    return JsonResponse(
        {
            "success": False,
            "message": "فشل التحقق من صحة البيانات المدخلة",
            "errors": error_list,
            "data": {},
        },
        status=422,
    )


@api.exception_handler(Exception)
def on_generic_error(request, exc):
    """Ensure unexpected runtime exceptions return the unified response envelope with 500."""
    logger.error(f"Unhandled API error: {exc}", exc_info=True)
    return JsonResponse(
        {
            "success": False,
            "message": "حدث خطأ داخلي غير متوقع في الخادم",
            "errors": [str(exc)],
            "data": {},
        },
        status=500,
    )


# Register all domain routers
api.add_router("/auth", auth_router, tags=["Authentication & Profile"])
api.add_router("/medical-cases", cases_router, tags=["Medical Cases"])
api.add_router("/treatment-plans", plans_router, tags=["AI Treatment Plans"])
api.add_router("/courses", courses_router, tags=["Courses & Video Academy"])
api.add_router("/payments", payments_router, tags=["Payments & Receipts"])
api.add_router("/games", games_router, tags=["Educational Games Store & COD"])
api.add_router("/articles", articles_router, tags=["Articles & Health Knowledge Base"])
api.add_router("/notifications", notifications_router, tags=["Real-Time Notifications"])
api.add_router("/users", users_router, tags=["User & Doctor Management"])
api.add_router("/geo", geo_router, tags=["Algerian Geographic Data"])
api.add_router("/analytics", analytics_router, tags=["Admin Dashboard Analytics"])
