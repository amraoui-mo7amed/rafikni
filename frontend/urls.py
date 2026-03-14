from frontend.views import main, courses
from django.urls import path

app_name = "frontend"
urlpatterns = [
    path("", main.index, name="index"),
    path("courses/", courses.course_list, name="course_list"),
    path("courses/<int:course_id>/", courses.course_detail, name="course_detail"),
]
