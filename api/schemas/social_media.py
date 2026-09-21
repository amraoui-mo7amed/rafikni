"""
Pydantic Schemas for Platform Social Media and Contact Information.
"""

from typing import Optional
from ninja import Schema


class SocialMediaSchema(Schema):
    """Schema representing social media handles and official platform contact channels."""

    facebook: Optional[str] = ""
    tiktok: Optional[str] = ""
    instagram: Optional[str] = ""
    email: Optional[str] = ""
    youtube: Optional[str] = ""
    phone: Optional[str] = ""
