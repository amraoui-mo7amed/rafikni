from django.shortcuts import render
from dashboard.models import Course, Article, Game


def index(request):
    latest_courses = Course.objects.filter(is_active=True)[:6]
    latest_articles = Article.objects.filter(is_published=True).order_by("-created_at")[
        :3
    ]
    latest_games = Game.objects.filter(is_active=True).order_by("-created_at")[:3]
    context = {
        "latest_courses": latest_courses,
        "latest_articles": latest_articles,
        "latest_games": latest_games,
    }
    return render(request, "index.html", context)
