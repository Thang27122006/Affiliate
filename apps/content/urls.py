from django.urls import path
from .views import article_list_view, article_detail_view

app_name = "content"

urlpatterns = [
    path("bai-viet/", article_list_view, name="article_list"),
    path("bai-viet/<slug:slug>/", article_detail_view, name="article_detail"),
]
