from django.urls import path
from .views import home_view, about_view, search_view, health_check_view

app_name = "core"

urlpatterns = [
    path("", home_view, name="home"),
    path("gioi-thieu/", about_view, name="about"),
    path("tim-kiem/", search_view, name="search"),
    path("health/", health_check_view, name="health_check"),
]
