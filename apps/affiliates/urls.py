from django.urls import path
from . import views

app_name = "affiliates"

urlpatterns = [
    path("go/<int:offer_id>/", views.redirect_offer_view, name="redirect_to_offer"),
]
