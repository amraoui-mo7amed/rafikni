"""
Admin Dashboard Analytics Router for Rafikni Platform.
Provides high-level KPIs, growth metrics, and pending action counts.
"""

from datetime import timedelta
from ninja import Router
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone

from user_auth.models import UserProfile
from dashboard.models import Payment, GameOrder
from api.security import AdminAuth
from api.utils import api_response
from api.schemas.common import ApiResponseSchema
from api.schemas.analytics import AnalyticsOverviewSchema

router = Router()


@router.get("/overview", auth=AdminAuth(), response=ApiResponseSchema[AnalyticsOverviewSchema])
def get_analytics_overview(request):
    """
    Admin: Retrieve platform growth metrics, role distribution, and pending review counts.
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    users_this_month = User.objects.filter(date_joined__gte=current_month).count()

    last_month = (current_month - timedelta(days=1)).replace(day=1)
    users_last_month = User.objects.filter(
        date_joined__gte=last_month, date_joined__lt=current_month
    ).count()

    if users_last_month > 0:
        growth = ((users_this_month - users_last_month) / users_last_month) * 100
    else:
        growth = 100.0 if users_this_month > 0 else 0.0

    roles_query = UserProfile.objects.values("role").annotate(count=Count("role"))
    role_map = dict(UserProfile.RoleChoices.choices)
    users_by_role = [
        {
            "role": r["role"],
            "role_display": role_map.get(r["role"], r["role"]),
            "count": r["count"],
        }
        for r in roles_query
    ]

    pending_payments = Payment.objects.filter(status=Payment.PaymentStatus.PENDING).count()
    pending_orders = GameOrder.objects.filter(status=GameOrder.OrderStatus.PENDING).count()

    data = {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "users_this_month": users_this_month,
        "users_growth": round(growth, 1),
        "users_by_role": users_by_role,
        "pending_payments": pending_payments,
        "pending_orders": pending_orders,
    }

    return api_response(success=True, message="تم جلب الإحصائيات بنجاح", data=data, status=200)
