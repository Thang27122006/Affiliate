from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from apps.catalog.models import Category, Product, StatusChoices
from apps.content.models import Article, ArticleTypeChoices
from apps.content.admin import ArticleAdmin

User = get_user_model()


class ContentAndAdminConstraintsTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Bàn phím",
            slug="ban-phim",
            status=StatusChoices.PUBLISHED,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="EK387",
            brand="E-Dra",
            slug="e-dra-ek387",
            status=StatusChoices.PUBLISHED,
        )
        self.author = User.objects.create_user(
            username="writer1",
            password="WriterPassword123!",
            is_staff=True,
        )
        self.superuser = User.objects.create_superuser(
            username="admin1",
            password="AdminPassword123!",
            email="admin1@example.com",
        )
        self.site = AdminSite()
        self.factory = RequestFactory()

    def test_safe_markdown_sanitization(self):
        """Kiểm tra nội dung HTML không an toàn trong Markdown bị lọc sạch (XSS Protection)"""
        malicious_markdown = (
            "# Tiêu đề an toàn\n\n"
            "Đoạn văn bình thường với [liên kết](https://example.com).\n\n"
            "<script>alert('Mã độc XSS')</script>\n"
            "<a href=\"javascript:evil()\" onclick=\"stealCookie()\">Nhấn vào đây</a>"
        )
        article = Article(
            title="Bài viết kiểm thử XSS",
            author=self.author,
            content=malicious_markdown,
        )
        safe_html = article.get_safe_content_html()
        self.assertNotIn("<script>", safe_html)
        self.assertNotIn("alert('Mã độc XSS')", safe_html)
        self.assertNotIn("javascript:evil()", safe_html)
        self.assertNotIn("onclick=", safe_html)
        self.assertIn("Tiêu đề an toàn", safe_html)
        self.assertIn('rel="noopener noreferrer"', safe_html)

    def test_article_product_relationship(self):
        """Kiểm tra liên kết bài viết với các sản phẩm được đề cập"""
        article = Article.objects.create(
            title="Đánh giá bàn phím E-Dra",
            author=self.author,
            content="Nội dung đánh giá thực tế.",
        )
        article.products.add(self.product)
        self.assertIn(self.product, article.products.all())
        self.assertIn(article, self.product.articles.all())

    def test_admin_auto_assigns_author(self):
        """Admin tự động gán tác giả là user đang đăng nhập nếu chưa chọn tác giả"""
        article_admin = ArticleAdmin(Article, self.site)
        article = Article(
            title="Bài viết chưa chọn tác giả",
            content="Nội dung kiểm tra.",
        )
        request = self.factory.post("/admin/content/article/add/")
        request.user = self.author
        article_admin.save_model(request, article, form=None, change=False)
        self.assertEqual(article.author, self.author)

    def test_permission_restriction_on_publishing(self):
        """User không có quyền can_publish_article không thể tự ý chuyển bài viết sang xuất bản"""
        article_admin = ArticleAdmin(Article, self.site)
        draft_article = Article.objects.create(
            title="Bài nháp chưa được duyệt",
            author=self.author,
            content="Nội dung.",
            status=StatusChoices.DRAFT,
        )
        request = self.factory.get(f"/admin/content/article/{draft_article.pk}/change/")
        request.user = self.author  # Staff thông thường không có quyền can_publish_article

        readonly_fields = article_admin.get_readonly_fields(request, draft_article)
        self.assertIn("status", readonly_fields)
        self.assertIn("published_at", readonly_fields)

        # Superuser thì không bị giới hạn readonly
        request.user = self.superuser
        superuser_readonly = article_admin.get_readonly_fields(request, draft_article)
        self.assertNotIn("status", superuser_readonly)
