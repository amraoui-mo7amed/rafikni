"""
Pydantic Schemas for User Management and Doctor Creation.
"""

from typing import List, Optional
from ninja import Schema
from .common import PaginationMetaSchema


class UserListItemSchema(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    role_display: str
    is_active: bool
    phone_number: Optional[str] = None
    birthdate: Optional[str] = None
    date_joined: str
    last_login: Optional[str] = None


class PaginatedUsersSchema(Schema):
    items: List[UserListItemSchema]
    pagination: PaginationMetaSchema
