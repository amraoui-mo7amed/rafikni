"""
Pydantic Schemas for AI-Generated Treatment Plans.
"""

from typing import Any, Dict, List, Optional
from ninja import Schema


class PlanSectionSchema(Schema):
    title: str
    icon: Optional[str] = "clipboard-list"
    content: Optional[str] = ""
    steps: Optional[List[str]] = []


class TreatmentPlanSchema(Schema):
    id: int
    case_type: str
    case_id: int
    patient_name: Optional[str] = ""
    age: Optional[int] = 0
    category: Optional[str] = "child"
    plan_data: Dict[str, Any]
    created_at: str
    updated_at: str
    created_by: Optional[str] = None
