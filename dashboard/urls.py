from django.urls import path
from dashboard.views import main, settings

app_name = "dashboard"

urlpatterns = [
    path("", main.index, name="index"),
    path("settings/email/", settings.email_settings, name="email_settings"),
    path(
        "settings/email/test/",
        settings.test_email_connection,
        name="test_email_connection",
    ),
]
