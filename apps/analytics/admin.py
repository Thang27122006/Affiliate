from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ClickEvent, PageView, AffiliateConversion, ConversionStatusChoices
from apps.affiliates.models import LinkModeChoices


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_link",
        "merchant_name",
        "link_mode_badge",
        "referrer_path_display",
        "created_at",
    )
    list_filter = ("link_mode", "created_at", "offer__merchant")
    search_fields = ("offer__product__name", "offer__merchant__name", "referrer_path")
    readonly_fields = ("offer", "link_mode", "referrer_path", "created_at")
    list_per_page = 30
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def product_link(self, obj):
        return obj.offer.product.name
    product_link.short_description = "Sản phẩm"

    def merchant_name(self, obj):
        return obj.offer.merchant.name
    merchant_name.short_description = "Nơi bán"

    def link_mode_badge(self, obj):
        if obj.link_mode == LinkModeChoices.REDIRECT:
            return format_html(
                '<span style="background-color: #fef3c7; color: #b45309; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;">'
                '🔀 Chuyển hướng</span>'
            )
        return format_html(
            '<span style="background-color: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;">'
            '🔗 Trực tiếp</span>'
        )
    link_mode_badge.short_description = "Hình thức liên kết"

    def referrer_path_display(self, obj):
        if obj.referrer_path:
            return obj.referrer_path
        return format_html('<span style="color: #94a3b8; font-style: italic;">Không xác định</span>')
    referrer_path_display.short_description = "Trang nguồn"


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("id", "target_display", "path", "created_at")
    list_filter = ("created_at",)
    search_fields = ("path", "product__name", "article__title")
    readonly_fields = ("product", "article", "path", "created_at")
    list_per_page = 30
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def target_display(self, obj):
        if obj.product:
            return format_html("🏷️ Sản phẩm: <strong>{}</strong>", obj.product.name)
        if obj.article:
            return format_html("📝 Bài viết: <strong>{}</strong>", obj.article.title)
        return format_html("📄 Đường dẫn: {}", obj.path)
    target_display.short_description = "Nội dung xem"


@admin.register(AffiliateConversion)
class AffiliateConversionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "program_name",
        "external_transaction_id",
        "external_order_item_id",
        "commission_display",
        "status_badge",
        "matched_target_display",
        "transaction_time",
    )
    list_filter = ("status", "currency", "program_name", "transaction_time")
    search_fields = (
        "external_transaction_id",
        "external_order_item_id",
        "tracking_code",
        "matched_product__name",
        "matched_article__title",
    )
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 30
    date_hierarchy = "transaction_time"

    def commission_display(self, obj):
        return f"{obj.commission_amount:,.2f} {obj.currency}"
    commission_display.short_description = "Hoa hồng"

    def status_badge(self, obj):
        if obj.status == ConversionStatusChoices.APPROVED:
            return format_html('<span style="color: #10b981; font-weight: 600;">✓ Đã duyệt</span>')
        elif obj.status == ConversionStatusChoices.PENDING:
            return format_html('<span style="color: #f59e0b; font-weight: 600;">⏳ Chờ duyệt</span>')
        return format_html('<span style="color: #ef4444; font-weight: 600;">✕ Bị từ chối</span>')
    status_badge.short_description = "Trạng thái"

    def matched_target_display(self, obj):
        if obj.matched_product:
            return format_html("🏷️ {}", obj.matched_product.name)
        if obj.matched_article:
            return format_html("📝 {}", obj.matched_article.title)
        if obj.tracking_code:
            return format_html('<span style="color: #64748b; font-size: 0.82rem;">Tag: {}</span>', obj.tracking_code)
        return format_html('<span style="color: #94a3b8; font-style: italic;">Chưa đối chiếu</span>')
    matched_target_display.short_description = "Sản phẩm / Bài viết khớp"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        dashboard_url = reverse("analytics:dashboard")
        import_url = reverse("analytics:reconciliation_import")
        extra_context["quick_links"] = format_html(
            '<div style="margin-bottom: 16px; padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; display: flex; gap: 12px; align-items: center;">'
            '<strong>⚡ Phím tắt Quản trị:</strong>'
            '<a href="{}" class="button" style="background: #2563eb; color: white;">📊 Xem Báo Cáo Hiệu Quả & CTR</a>'
            '<a href="{}" class="button" style="background: #059669; color: white;">📥 Nhập Báo Cáo Đối Soát CSV</a>'
            '</div>',
            dashboard_url,
            import_url,
        )
        return super().changelist_view(request, extra_context=extra_context)
