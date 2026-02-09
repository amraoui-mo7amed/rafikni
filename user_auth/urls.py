from user_auth.views import auth

from django.urls import path

app_name = "user_auth"
urlpatterns = [
    path("login/", auth.login_view, name="login"),
    path("signup/", auth.signup_view, name="signup"),
    path("lost-password/", auth.lost_password_view, name="lost_password"),
    path("logout/", auth.logout_view, name="logout"),
]
