from django.urls import path
from .views import home_view, health_check_view

app_name = "core"

urlpatterns = [
    path("", home_view, name="home"),
    path("health/", health_check_view, name="health_check"),
]
