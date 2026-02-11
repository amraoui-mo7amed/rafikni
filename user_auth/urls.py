from user_auth.views import auth

from django.urls import path

app_name = "user_auth"
urlpatterns = [
    path("login/", auth.login_view, name="login"),
    path("signup/", auth.signup_view, name="signup"),
    path("activate/<uidb64>/<token>/", auth.activate_view, name="activate"),
    path("lost-password/", auth.lost_password_view, name="lost_password"),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
    path("logout/", auth.logout_view, name="logout"),
]
