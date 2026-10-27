from django.contrib import admin
from django.utils.html import format_html
from .models import Merchant, Offer


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("name", "website_link", "is_active_badge", "is_demo", "offer_count", "created_at")
    list_filter = ("is_active", "is_demo", "created_at")
    search_fields = ("name", "slug", "website", "allowed_hostnames")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25

    def website_link(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', obj.website, obj.website)
    website_link.short_description = "Website"

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
    list_display = ("product", "merchant", "price_display", "is_active_badge", "price_checked_at", "is_demo")
    list_filter = ("merchant", "is_active", "is_demo", "currency")
    search_fields = ("product__name", "merchant__name", "affiliate_url")
    list_per_page = 25
    autocomplete_fields = ["merchant"]

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
