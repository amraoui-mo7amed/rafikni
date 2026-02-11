from django.urls import path
from dashboard.views import main, settings, users

app_name = "dashboard"

urlpatterns = [
    path("", main.index, name="index"),
    # User Management
    path("users/", users.user_list, name="user_list"),
    path("users/<int:pk>/", users.user_detail, name="user_detail"),
    path("users/<int:pk>/delete/", users.user_delete, name="user_delete"),
    path(
        "users/<int:pk>/toggle-status/",
        users.user_toggle_status,
        name="user_toggle_status",
    ),
    path("profile/update/", users.profile_update, name="profile_update"),
    path("settings/email/", settings.email_settings, name="email_settings"),
    path(
        "settings/email/test/",
        settings.test_email_connection,
        name="test_email_connection",
    ),
]
