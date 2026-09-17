"""
Pydantic Schemas for Generic Payments and Receipt Verification.
"""

from typing import Any, Dict, List, Optional
from ninja import Schema
from .common import PaginationMetaSchema


class PaymentDetailSchema(Schema):
    id: int
    user_id: int
    user_username: str
    user_email: str
    user_full_name: Optional[str] = None
    target_type: str
    target_id: int
    target_title: str
    receipt_image_url: Optional[str] = None
    status: str
    status_display: str
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None


class PaginatedPaymentsSchema(Schema):
    items: List[PaymentDetailSchema]
    pagination: PaginationMetaSchema


class ReviewPaymentSchema(Schema):
    action: str  # "approve" | "reject"
