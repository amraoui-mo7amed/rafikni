"""
Articles & Health Knowledge Base Router for Rafikni Platform.
Endpoints for public health articles, pregnancy/childhood category filters, and admin content publishing.
"""

from typing import List, Optional
from ninja import Router, Form, File, UploadedFile
from django.utils.text import slugify
from django.db.models import Q

from dashboard.models import Article
from api.security import AdminAuth
from api.utils import api_response
from api.serializers import serialize_article
from api.schemas.common import ApiResponseSchema
from api.schemas.cases import ChoiceItemSchema
from api.schemas.articles import (
    ArticleCardSchema,
    ArticleDetailSchema,
)

router = Router()


@router.get("/categories", response=ApiResponseSchema[List[ChoiceItemSchema]])
def list_article_categories(request):
    """
    List medical stage categories for articles (Before, During, After birth).
    """
    items = [
        {"value": val, "label": label}
        for val, label in Article.CategoryChoices.choices
    ]
    return api_response(success=True, message="تم جلب الفئات بنجاح", data=items, status=200)


@router.get("/", response=ApiResponseSchema[List[ArticleCardSchema]])
def list_articles(
    request,
    category: Optional[str] = None,
    q: Optional[str] = None,
):
    """
    Public catalog of published health and educational articles.
    """
    articles = Article.objects.filter(is_published=True).select_related("author").order_by("-created_at")

    if category and category in Article.CategoryChoices.values:
        articles = articles.filter(category=category)

    if q:
        articles = articles.filter(
            Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__icontains=q)
        )

    items = [serialize_article(a, request) for a in articles]
    return api_response(success=True, message="تم جلب المقالات بنجاح", data=items, status=200)


@router.get("/{slug}", response={200: ApiResponseSchema[ArticleDetailSchema], 404: ApiResponseSchema[None]})
def get_article_detail(request, slug: str):
    """
    Full article reader with related articles from the same medical stage.
    """
    try:
        article = Article.objects.select_related("author").get(slug=slug, is_published=True)
    except Article.DoesNotExist:
        return api_response(success=False, message="المقال غير موجود", errors=["المقال غير موجود"], status=404)

    related = (
        Article.objects.filter(category=article.category, is_published=True)
        .exclude(id=article.id)
        .select_related("author")[:6]
    )

    data = serialize_article(article, request, include_content=True)
    data["related_articles"] = [serialize_article(r, request) for r in related]

    return api_response(success=True, message="تم جلب تفاصيل المقال بنجاح", data=data, status=200)


# ---------------- Admin Operations ----------------

@router.post("/", auth=AdminAuth(), response={201: ApiResponseSchema[ArticleCardSchema], 400: ApiResponseSchema[None]})
def create_article(
    request,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    tags: Optional[str] = Form(""),
    is_published: bool = Form(False),
    thumbnail: Optional[UploadedFile] = File(None),
):
    """Admin: Publish or draft a new article."""
    if category not in Article.CategoryChoices.values:
        return api_response(success=False, message="فئة المقال غير صالحة", errors=["فئة المقال غير صالحة"], status=400)

    try:
        slug = slugify(title, allow_unicode=True)
        original_slug = slug
        counter = 1
        while Article.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        article = Article.objects.create(
            title=title,
            slug=slug,
            content=content,
            category=category,
            tags=tags or "",
            thumbnail=thumbnail,
            author=request.user,
            is_published=is_published,
        )
        return api_response(
            success=True,
            message="تم إنشاء المقال بنجاح",
            data=serialize_article(article, request),
            status=201,
        )
    except Exception as e:
        return api_response(success=False, message="فشل إنشاء المقال", errors=[str(e)], status=400)


@router.delete("/{article_id}", auth=AdminAuth(), response={200: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def delete_article(request, article_id: int):
    """Admin: Delete an article."""
    try:
        article = Article.objects.get(id=article_id)
        article.delete()
        return api_response(success=True, message="تم حذف المقال بنجاح", status=200)
    except Article.DoesNotExist:
        return api_response(success=False, message="المقال غير موجود", errors=["المقال غير موجود"], status=404)
