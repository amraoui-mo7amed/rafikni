"""
Pydantic Schemas for Algerian Geographic Data (Wilayas and Communes).
"""

from ninja import Schema


class WilayaSchema(Schema):
    code: str
    name: str


class CommuneSchema(Schema):
    id: int
    name: str
