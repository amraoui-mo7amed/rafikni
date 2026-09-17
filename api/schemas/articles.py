"""
Pydantic Schemas for Educational Articles and Health Blog.
"""

from typing import List, Optional
from ninja import Schema


class ArticleCardSchema(Schema):
    id: int
    title: str
    slug: str
    category: str
    category_display: str
    excerpt: str
    thumbnail: Optional[str] = None
    tags: List[str] = []
    author_username: str
    is_published: bool
    created_at: str


class ArticleDetailSchema(Schema):
    id: int
    title: str
    slug: str
    category: str
    category_display: str
    content: str
    thumbnail: Optional[str] = None
    tags: List[str] = []
    author_username: str
    created_at: str
    updated_at: str
    related_articles: List[ArticleCardSchema] = []
