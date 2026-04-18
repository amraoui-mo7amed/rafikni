from django.shortcuts import render
from dashboard.models import Course, Article


def index(request):
    latest_courses = Course.objects.filter(is_active=True)[:6]
    latest_articles = Article.objects.filter(is_published=True).order_by("-created_at")[
        :3
    ]
    context = {
        "latest_courses": latest_courses,
        "latest_articles": latest_articles,
    }
    return render(request, "index.html", context)
