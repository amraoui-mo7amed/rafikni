"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.main import api as api_v1
import django_eventstream

urlpatterns = [
    path("", include("frontend.urls", namespace="frontend")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path("auth/", include("user_auth.urls", namespace="user_auth")),
    # RESTful API v1 powered by Django Ninja
    path("api/v1/", api_v1.urls),
    # EventStream endpoint - user-specific channels
    # Client selects channel via query parameter: ?channel=user-{user_id}
    path("events/", include(django_eventstream.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
