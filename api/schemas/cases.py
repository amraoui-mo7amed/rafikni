"""
Pydantic Schemas for Medical Cases.
"""

from typing import List, Optional, Tuple
from ninja import Schema
from .common import PaginationMetaSchema


class ChoiceItemSchema(Schema):
    value: str
    label: str


class CaseChoicesSchema(Schema):
    categories: List[ChoiceItemSchema]
    genders: List[ChoiceItemSchema]
    disability_levels: List[ChoiceItemSchema]


class CaseDetailSchema(Schema):
    id: int
    case_type: str
    case_type_display: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    gender_display: Optional[str] = None
    aphasie: bool = False
    is_approved: bool = False
    user_id: int
    user_username: str
    user_full_name: Optional[str] = None
    disorders: Optional[str] = None
    syndromes: Optional[str] = None
    intellectual_disability: Optional[str] = None
    intellectual_disability_display: Optional[str] = None
    alzheimer: Optional[bool] = None
    parkinson: Optional[bool] = None


class PaginatedCasesSchema(Schema):
    items: List[CaseDetailSchema]
    pagination: PaginationMetaSchema
