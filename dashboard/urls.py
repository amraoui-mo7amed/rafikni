from django.urls import path
from dashboard.views import main, settings, users, medical_cases

app_name = "dashboard"

urlpatterns = [
    path("", main.index, name="index"),
    # User Management
    path("users/", users.user_list, name="user_list"),
    path("users/create-doctor/", users.doctor_create, name="doctor_create"),
    path("users/<int:pk>/", users.user_detail, name="user_detail"),
    path("users/<int:pk>/delete/", users.user_delete, name="user_delete"),
    path(
        "users/<int:pk>/toggle-status/",
        users.user_toggle_status,
        name="user_toggle_status",
    ),
    path("profile/update/", users.profile_update, name="profile_update"),
    # Medical Cases
    path(
        "medical-cases/",
        medical_cases.medical_case_list,
        name="medical_case_list",
    ),
    path(
        "medical-cases/create/",
        medical_cases.medical_case_create,
        name="medical_case_create",
    ),
    path(
        "medical-cases/<str:case_type>/<int:case_id>/delete/",
        medical_cases.medical_case_delete,
        name="medical_case_delete",
    ),
    # Settings
    path("settings/email/", settings.email_settings, name="email_settings"),
    path(
        "settings/email/test/",
        settings.test_email_connection,
        name="test_email_connection",
    ),
]
