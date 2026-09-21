"""
Pydantic Schemas for Authentication and User Profiles.
"""

from typing import Optional
from ninja import Schema


class SignupSchema(Schema):
    username: Optional[str] = None
    email: str
    password: str
    confirm_password: str


class LoginSchema(Schema):
    username: str
    password: str


class RefreshTokenSchema(Schema):
    refresh_token: str


class ActivateSchema(Schema):
    uidb64: str
    token: str


class LostPasswordSchema(Schema):
    email: str


class PasswordResetConfirmSchema(Schema):
    uidb64: str
    token: str
    password: str
    confirm_password: str


class UserProfileOutSchema(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    role_display: str
    phone_number: Optional[str] = None
    birthdate: Optional[str] = None
    profile_pic: Optional[str] = None
    is_active: bool
    date_joined: str


class TokenResponseSchema(Schema):
    access_token: str
    refresh_token: str
    user: UserProfileOutSchema
