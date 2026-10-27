from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "article_type",
        "author",
        "status_badge",
        "is_hands_on_badge",
        "published_at",
        "is_demo",
        "created_at",
    )
    list_filter = (
        "status",
        "article_type",
        "is_hands_on_experience",
        "is_demo",
        "published_at",
    )
    search_fields = ("title", "slug", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("products",)
    list_per_page = 25
    date_hierarchy = "published_at"

    fieldsets = (
        (
            "Thông tin cơ bản",
            {
                "fields": (
                    "title",
                    "slug",
                    "article_type",
                    "author",
                    "thumbnail",
                    "summary",
                )
            },
        ),
        (
            "Nội dung bài viết",
            {
                "fields": ("content",),
                "description": "Nhập nội dung dưới định dạng Markdown chuẩn. Hệ thống sẽ tự động làm sạch an toàn khi hiển thị.",
            },
        ),
        (
            "Sản phẩm liên kết",
            {
                "fields": ("products",),
                "description": "Chọn các sản phẩm phụ kiện sinh viên được đánh giá hoặc so sánh trong bài viết.",
            },
        ),
        (
            "Biên tập minh bạch (Editorial Transparency)",
            {
                "fields": (
                    "is_hands_on_experience",
                    "testing_methodology",
                    "testing_duration",
                    "information_source",
                    "affiliate_disclosure",
                ),
                "classes": ("collapse",),
                "description": "Các trường bắt buộc công khai nhằm đảm bảo tính trung thực và minh bạch của bài đánh giá.",
            },
        ),
        (
            "Quản lý xuất bản",
            {
                "fields": ("status", "published_at", "is_demo"),
            },
        ),
    )

    def status_badge(self, obj):
        if obj.status == "published":
            return format_html('<span style="color: #10b981; font-weight: 600;">● Đã xuất bản</span>')
        return format_html('<span style="color: #94a3b8; font-weight: 600;">○ Bản nháp</span>')
    status_badge.short_description = "Trạng thái"

    def is_hands_on_badge(self, obj):
        if obj.is_hands_on_experience:
            return format_html('<span style="color: #06b6d4; font-weight: 600;">✓ Trực tiếp test</span>')
        return format_html('<span style="color: #94a3b8;">Tổng hợp thông tin</span>')
    is_hands_on_badge.short_description = "Trải nghiệm thực tế"

    def save_model(self, request, obj, form, change):
        # Tự động gán tác giả là user hiện tại nếu chưa chọn tác giả
        if not obj.author_id:
            obj.author = request.user
        
        # Nếu chuyển sang xuất bản và chưa có ngày xuất bản, tự động gán ngày hiện tại
        if obj.status == "published" and not obj.published_at:
            obj.published_at = timezone.now()
            
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # Chỉ người có quyền 'content.can_publish_article' hoặc superuser mới được xuất bản bài viết
        can_publish = request.user.is_superuser or request.user.has_perm("content.can_publish_article")
        if not can_publish:
            if obj and obj.status == "draft":
                readonly.append("status")
                readonly.append("published_at")
        return readonly
