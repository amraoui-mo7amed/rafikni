"""
Pydantic Schemas for Educational Games and COD Orders.
"""

from typing import List, Optional
from ninja import Schema


class GameCardSchema(Schema):
    id: int
    title: str
    slug: str
    price: float
    description: str
    tags: List[str] = []
    thumbnail: Optional[str] = None
    is_active: bool = True


class GameDetailSchema(Schema):
    id: int
    title: str
    slug: str
    price: float
    description: str
    tags: List[str] = []
    thumbnail: Optional[str] = None
    gallery_images: List[str] = []
    is_active: bool = True


class PlaceOrderSchema(Schema):
    game_id: int
    full_name: str
    phone_number: str
    wilaya: str
    commune: str
    address: str


class GameOrderSchema(Schema):
    id: int
    game_id: int
    game_title: str
    full_name: str
    phone_number: str
    wilaya: str
    commune: str
    address: str
    status: str
    status_display: str
    user_id: Optional[int] = None
    created_at: str


class UpdateOrderStatusSchema(Schema):
    status: str  # "pending", "confirmed", "delivered", "cancelled"
