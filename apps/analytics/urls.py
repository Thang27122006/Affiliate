from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("api/click/", views.track_click_api_view, name="track_click_api"),
    path("dashboard/", views.analytics_dashboard_view, name="dashboard"),
    path("reconciliation/import/", views.reconciliation_import_view, name="reconciliation_import"),
    path("reconciliation/sample-csv/", views.download_sample_csv_view, name="download_sample_csv"),
]
