from django.urls import path
from .views import (
    category_detail_view,
    product_compare_view,
    product_detail_view,
    product_list_view,
)

app_name = "catalog"

urlpatterns = [
    path("san-pham/", product_list_view, name="product_list"),
    path("so-sanh/", product_compare_view, name="compare"),
    path("danh-muc/<slug:slug>/", category_detail_view, name="category_detail"),
    path("san-pham/<slug:slug>/", product_detail_view, name="product_detail"),
]
