from frontend.views import main, courses, articles, games
from django.urls import path, re_path

app_name = "frontend"
urlpatterns = [
    path("", main.index, name="index"),
    path("courses/", courses.course_list, name="course_list"),
    path("courses/<int:course_id>/", courses.course_detail, name="course_detail"),
    path("articles/", articles.article_list, name="article_list"),
    re_path(r"^articles/(?P<slug>[-\w]+)/$", articles.article_detail, name="article_detail"),
    # Games
    path("games/", games.game_list, name="game_list"),
    re_path(r"^games/(?P<slug>[-\w]+)/$", games.game_detail, name="game_detail"),
    path("games/api/communes/", games.get_communes_ajax, name="get_communes_ajax"),
    path("games/api/order/", games.place_order, name="place_game_order"),
]

