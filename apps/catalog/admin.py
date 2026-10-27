from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django import forms
from .models import Category, Product, ProductImage, SpecificationDefinition, ProductSpecification
from apps.affiliates.models import Offer


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "display_order")


class ProductSpecificationInlineForm(forms.ModelForm):
    class Meta:
        model = ProductSpecification
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Giới hạn định nghĩa thông số thuộc đúng danh mục của sản phẩm nếu đã có sản phẩm
        if self.instance and hasattr(self.instance, "product") and self.instance.product_id:
            self.fields["specification_definition"].queryset = (
                SpecificationDefinition.objects.filter(category=self.instance.product.category)
            )


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    form = ProductSpecificationInlineForm
    extra = 1
    fields = ("specification_definition", "value")


class OfferInline(admin.TabularInline):
    model = Offer
    extra = 1
    fields = ("merchant", "price", "currency", "affiliate_url", "is_active", "price_checked_at")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "slug", "status_badge", "is_demo", "product_count", "created_at")
    list_editable = ("display_order",)
    list_filter = ("status", "is_demo", "created_at")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Số sản phẩm"

    def status_badge(self, obj):
        if obj.status == "published":
            return format_html('<span style="color: #10b981; font-weight: 600;">● Đã xuất bản</span>')
        return format_html('<span style="color: #94a3b8; font-weight: 600;">○ Bản nháp</span>')
    status_badge.short_description = "Trạng thái"


@admin.register(SpecificationDefinition)
class SpecificationDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "category", "data_type", "unit", "display_order")
    list_filter = ("category", "data_type")
    search_fields = ("name", "key")
    list_per_page = 25


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "model", "category", "status_badge", "is_demo", "created_at")
    list_filter = ("category", "status", "brand", "is_demo")
    search_fields = ("name", "brand", "model", "slug")
    prepopulated_fields = {"slug": ("brand", "name")}
    inlines = [ProductImageInline, ProductSpecificationInline, OfferInline]
    list_per_page = 25

    def status_badge(self, obj):
        if obj.status == "published":
            return format_html('<span style="color: #10b981; font-weight: 600;">● Đã xuất bản</span>')
        return format_html('<span style="color: #94a3b8; font-weight: 600;">○ Bản nháp</span>')
    status_badge.short_description = "Trạng thái"

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # Kiểm tra quyền xuất bản sản phẩm
        if not (request.user.is_superuser or request.user.has_perm("catalog.can_publish_product")):
            if obj and obj.status == "draft":
                readonly.append("status")
        return readonly


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text", "display_order", "created_at")
    list_filter = ("product__category",)
    search_fields = ("product__name", "alt_text")
    list_per_page = 25


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ("product", "specification_definition", "value")
    list_filter = ("specification_definition__category",)
    search_fields = ("product__name", "specification_definition__name", "value")
    list_per_page = 25
