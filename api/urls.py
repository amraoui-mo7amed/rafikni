"""
URL Routing for Rafikni API v1.
Exposes NinjaAPI endpoints.
"""

from django.urls import path
from .main import api

app_name = "api_v1"

urlpatterns = [
    path("", api.urls),
]
