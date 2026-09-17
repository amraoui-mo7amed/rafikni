"""
Pydantic Schemas for Admin Dashboard Analytics.
"""

from typing import List
from ninja import Schema


class RoleCountSchema(Schema):
    role: str
    role_display: str
    count: int


class AnalyticsOverviewSchema(Schema):
    total_users: int
    active_users: int
    inactive_users: int
    users_this_month: int
    users_growth: float
    users_by_role: List[RoleCountSchema]
    pending_payments: int = 0
    pending_orders: int = 0
