from frontend.views import main 
from django.urls import path

app_name = "frontend"
urlpatterns = [
    path('', main.index, name='index'),
]