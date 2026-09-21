"""
Real-Time Notifications Router for Rafikni Platform.
Endpoints for checking unread count, listing alerts, and updating read status.
"""

from typing import List
from datetime import datetime
from ninja import Router

from dashboard.models import Notification
from api.security import JWTAuth
from api.utils import api_response
from api.serializers import serialize_notification
from api.schemas.common import ApiResponseSchema
from api.schemas.notifications import NotificationSchema, NotificationCreateSchema

router = Router()


@router.post("/", auth=JWTAuth(), response={201: ApiResponseSchema[NotificationSchema], 400: ApiResponseSchema[None]})
def create_user_notification(request, payload: NotificationCreateSchema):
    """
    Create a notification. If user_id is provided, sends to that user; otherwise to current user.
    Dispatches real-time SSE eventstream notification.
    """
    from django.contrib.auth import get_user_model
    from dashboard.utils import create_notification
    User = get_user_model()
    target_user = request.user
    if payload.user_id:
        try:
            target_user = User.objects.get(id=payload.user_id)
        except User.DoesNotExist:
            return api_response(success=False, message="المستخدم المحدد غير موجود", status=400)

    notif = create_notification(
        user=target_user,
        title=payload.title,
        message=payload.message,
        notification_type=payload.type or "info",
        link=payload.link or "",
    )
    if not notif:
        return api_response(success=False, message="فشل إنشاء الإشعار", status=400)

    return api_response(
        success=True,
        message="تم إنشاء وإرسال الإشعار بنجاح",
        data=serialize_notification(notif),
        status=201,
    )


@router.get("/unread-count", auth=JWTAuth(), response=ApiResponseSchema[dict])
def get_unread_count(request):
    """
    Get the total count of unread notifications for the current authenticated user.
    """
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return api_response(success=True, message="تم جلب عدد الإشعارات", data={"count": count}, status=200)


@router.get("/", auth=JWTAuth(), response=ApiResponseSchema[List[NotificationSchema]])
def list_notifications(request):
    """
    List the latest 50 notifications for the current authenticated user.
    """
    notifications = Notification.objects.filter(user=request.user)[:50]
    items = [serialize_notification(n) for n in notifications]
    return api_response(success=True, message="تم جلب الإشعارات بنجاح", data=items, status=200)



@router.post("/{notification_id}/read", auth=JWTAuth(), response={200: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def mark_as_read(request, notification_id: int):
    """
    Mark a specific notification as read.
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now()
            notification.save()
        return api_response(success=True, message="تم تعيين الإشعار كمقروء", status=200)
    except Notification.DoesNotExist:
        return api_response(success=False, message="الإشعار غير موجود", errors=["الإيصال غير موجود"], status=404)


@router.post("/mark-all-read", auth=JWTAuth(), response=ApiResponseSchema[None])
def mark_all_as_read(request):
    """
    Mark all unread notifications as read for the current user.
    """
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=datetime.now()
    )
    return api_response(success=True, message="تم تعيين جميع الإشعارات كمقروءة", status=200)


@router.delete("/{notification_id}", auth=JWTAuth(), response={200: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def delete_notification(request, notification_id: int):
    """
    Delete a specific notification for the current user.
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return api_response(success=True, message="تم حذف الإشعار بنجاح", status=200)
    except Notification.DoesNotExist:
        return api_response(success=False, message="الإشعار غير موجود", errors=["الإشعار غير موجود"], status=404)
