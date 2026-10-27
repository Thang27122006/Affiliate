from django.contrib import admin
from django.utils.html import format_html
from .models import Merchant, Offer, LinkModeChoices, OfferLinkModeChoices


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "link_mode_badge",
        "website_link",
        "is_active_badge",
        "is_demo",
        "offer_count",
        "created_at",
    )
    list_filter = ("link_mode", "is_active", "is_demo", "created_at")
    search_fields = ("name", "slug", "website", "allowed_hostnames")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25

    def website_link(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', obj.website, obj.website)
    website_link.short_description = "Website"

    def link_mode_badge(self, obj):
        if obj.link_mode == LinkModeChoices.REDIRECT:
            return format_html(
                '<span style="background-color: #fef3c7; color: #b45309; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;">'
                '🔀 Chuyển hướng nội bộ</span>'
            )
        return format_html(
            '<span style="background-color: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;">'
            '🔗 Trực tiếp (Direct)</span>'
        )
    link_mode_badge.short_description = "Chế độ liên kết"

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10b981; font-weight: 600;">● Hoạt động</span>')
        return format_html('<span style="color: #ef4444; font-weight: 600;">○ Tạm dừng</span>')
    is_active_badge.short_description = "Trạng thái"

    def offer_count(self, obj):
        return obj.offers.count()
    offer_count.short_description = "Số Offer liên kết"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "merchant",
        "effective_link_mode_badge",
        "price_display",
        "is_active_badge",
        "price_checked_at",
        "is_demo",
    )
    list_filter = ("link_mode", "merchant__link_mode", "merchant", "is_active", "is_demo", "currency")
    search_fields = ("product__name", "merchant__name", "affiliate_url")
    list_per_page = 25
    autocomplete_fields = ["merchant"]

    def effective_link_mode_badge(self, obj):
        mode = obj.get_effective_link_mode()
        override_note = " (override)" if obj.link_mode != OfferLinkModeChoices.USE_MERCHANT else ""
        if mode == LinkModeChoices.REDIRECT:
            return format_html(
                '<span style="background-color: #fef3c7; color: #b45309; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem;">'
                '🔀 Redirect{}</span>',
                override_note,
            )
        return format_html(
            '<span style="background-color: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem;">'
            '🔗 Direct{}</span>',
            override_note,
        )
    effective_link_mode_badge.short_description = "Chế độ áp dụng"

    def price_display(self, obj):
        if obj.price is not None:
            return f"{obj.price:,.0f} {obj.currency}"
        return format_html('<span style="color: #94a3b8; font-style: italic;">Chưa có giá</span>')
    price_display.short_description = "Giá tham khảo"

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10b981; font-weight: 600;">● Hoạt động</span>')
        return format_html('<span style="color: #ef4444; font-weight: 600;">○ Tạm dừng</span>')
    is_active_badge.short_description = "Trạng thái"

