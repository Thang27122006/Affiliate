"""
URL configuration for 'Góc Phụ Kiện' project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls", namespace="core")),
]

# Serve media and static files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site titles in Vietnamese
admin.site.site_header = "Góc Phụ Kiện - Quản trị hệ thống"
admin.site.site_title = "Quản trị Góc Phụ Kiện"
admin.site.index_title = "Bảng điều khiển quản trị"
