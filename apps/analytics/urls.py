from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("api/click/", views.track_click_api_view, name="track_click_api"),
]
