from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.catalog.models import Category, Product
from apps.content.models import Article


class StaticViewSitemap(Sitemap):
    """
    Sitemap cho các trang tĩnh quan trọng cần lập chỉ mục:
    Trang chủ, danh sách sản phẩm, danh sách bài viết, giới thiệu / phương pháp, chính sách riêng tư.
    """
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "core:home",
            "catalog:product_list",
            "content:article_list",
            "core:about",
            "core:privacy_policy",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    """
    Sitemap cho các danh mục phụ kiện đã xuất bản (status='published').
    """
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Category.objects.published().order_by("id")

    def location(self, obj):
        return reverse("catalog:category_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class ProductSitemap(Sitemap):
    """
    Sitemap cho các sản phẩm đã xuất bản (status='published').
    Chỉ lập chỉ mục các sản phẩm công khai, loại trừ bản nháp.
    """
    priority = 0.9
    changefreq = "daily"

    def items(self):
        return Product.objects.published().select_related("category").order_by("-updated_at")

    def location(self, obj):
        return reverse("catalog:product_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class ArticleSitemap(Sitemap):
    """
    Sitemap cho các bài viết đánh giá, cẩm nang đã xuất bản hợp lệ.
    Loại trừ bản nháp hoặc bài có lịch xuất bản tương lai.
    """
    priority = 0.85
    changefreq = "weekly"

    def items(self):
        return Article.objects.published().select_related("author").order_by("-published_at")

    def location(self, obj):
        return reverse("content:article_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at
