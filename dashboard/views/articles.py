from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.db import transaction
from ..models import Article
import json


@login_required
def article_list(request):
    """
    View to list all articles in the dashboard with filtering.
    """
    query = request.GET.get("q")
    category = request.GET.get("category")

    articles = Article.objects.all()

    if query:
        articles = articles.filter(title__icontains=query)

    if category:
        articles = articles.filter(category=category)

    context = {
        "articles": articles,
        "query": query,
        "category": category,
        "categories": Article.CategoryChoices.choices,
    }
    return render(request, "dashboard/articles/list.html", context)


@login_required
def article_create(request):
    """
    View to create a new article. Returns JsonResponse for AJAX POST requests.
    """
    if request.method == "POST":
        try:
            title = request.POST.get("title")
            content = request.POST.get("content")
            category = request.POST.get("category")
            tags = request.POST.get("tags", "")
            thumbnail = request.FILES.get("thumbnail")
            is_published = request.POST.get("is_published") == "on"

            if not title or not content or not category:
                return JsonResponse(
                    {"success": False, "errors": ["يرجى ملء جميع الحقول الإجبارية."]}
                )

            slug = slugify(title, allow_unicode=True)
            # Handle duplicate slugs
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
                tags=tags,
                thumbnail=thumbnail,
                author=request.user,
                is_published=is_published,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "تم إنشاء المقال بنجاح.",
                    "redirect_url": reverse("dashboard:article_list"),
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})

    context = {"categories": Article.CategoryChoices.choices}
    return render(request, "dashboard/articles/create.html", context)


@login_required
def article_edit(request, pk):
    """
    View to edit an existing article.
    """
    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        try:
            article.title = request.POST.get("title")
            article.content = request.POST.get("content")
            article.category = request.POST.get("category")
            article.tags = request.POST.get("tags", "")
            if request.FILES.get("thumbnail"):
                article.thumbnail = request.FILES.get("thumbnail")
            article.is_published = request.POST.get("is_published") == "on"

            article.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "تم تحديث المقال بنجاح.",
                    "redirect_url": reverse("dashboard:article_list"),
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})

    context = {
        "article": article,
        "categories": Article.CategoryChoices.choices,
    }
    return render(request, "dashboard/articles/edit.html", context)


@login_required
def article_delete(request, pk):
    """
    View to delete an article. Should be called via POST/AJAX with SweetAlert confirmation.
    """
    if request.method == "POST":
        try:
            article = get_object_or_404(Article, pk=pk)
            article.delete()
            return JsonResponse({"success": True, "message": "تم حذف المقال بنجاح."})
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})

    return JsonResponse({"success": False, "errors": ["طريقة الطلب غير صالحة."]})
