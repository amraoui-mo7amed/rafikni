"""
Pydantic Schemas for Notifications.
"""

from typing import Optional
from ninja import Schema


class NotificationSchema(Schema):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: str
    read_at: Optional[str] = None
    link: Optional[str] = ""


class NotificationCreateSchema(Schema):
    title: str
    message: str
    type: Optional[str] = "info"
    link: Optional[str] = ""
    user_id: Optional[int] = None

