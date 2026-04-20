from django.shortcuts import render, get_object_or_404
from dashboard.models import Article


def article_list(request):
    """
    Public view to list all published articles.
    """
    category = request.GET.get("category")
    articles = Article.objects.filter(is_published=True).order_by("-created_at")

    if category:
        articles = articles.filter(category=category)

    context = {
        "articles": articles,
        "category": category,
        "categories": Article.CategoryChoices.choices,
    }
    return render(request, "articles/list.html", context)


def article_detail(request, slug):
    """
    Public view for a single article.
    """
    article = get_object_or_404(Article, slug=slug, is_published=True)
    # Get related articles from same category
    related_articles = Article.objects.filter(
        category=article.category, is_published=True
    ).exclude(id=article.id)[:6]

    context = {"article": article, "related_articles": related_articles}
    return render(request, "articles/detail.html", context)
