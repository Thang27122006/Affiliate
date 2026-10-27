from django.contrib import admin
from django.utils.html import format_html
from .models import ClickEvent
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
        # Không cho phép tạo sự kiện click thủ công qua admin
        return False

    def has_change_permission(self, request, obj=None):
        # Dữ liệu log là bất biến (immutable), không cho phép chỉnh sửa
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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["disclaimer"] = (
            "⚠️ Lưu ý quan trọng: Số liệu trên bảng chỉ phản ánh số lượt bấm kỹ thuật (Clicks), "
            "không phải số người dùng duy nhất (Unique Visitors). Dữ liệu có thể bị sai lệch bởi "
            "bot crawl tự động hoặc các tiện ích mở rộng chặn quảng cáo / chặn tracking trên trình duyệt của độc giả."
        )
        return super().changelist_view(request, extra_context=extra_context)
