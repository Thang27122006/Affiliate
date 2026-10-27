from datetime import timedelta
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from django.urls import reverse
from apps.catalog.models import Category, Product, StatusChoices
from apps.content.models import Article, ArticleTypeChoices
from apps.content.admin import ArticleAdmin

User = get_user_model()


class ContentAndAdminConstraintsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
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
        self.article_published = Article.objects.create(
            title="Đánh giá bàn phím E-Dra EK387",
            slug="danh-gia-ban-phim-e-dra-ek387",
            author=self.author,
            content="Nội dung đánh giá thực tế.",
            article_type=ArticleTypeChoices.REVIEW,
            status=StatusChoices.PUBLISHED,
            published_at=timezone.now() - timedelta(days=1),
            is_hands_on_experience=True,
            testing_methodology="Gõ văn bản 8 tiếng/ngày trong 2 tuần.",
            testing_duration="2 tuần",
        )
        self.article_published.products.add(self.product)

        self.article_draft = Article.objects.create(
            title="Bài viết nháp chưa công khai",
            slug="bai-viet-nhap-chua-cong-khai",
            author=self.author,
            content="Nội dung nháp.",
            status=StatusChoices.DRAFT,
        )

        self.article_future = Article.objects.create(
            title="Bài viết hẹn giờ tương lai",
            slug="bai-viet-hen-gio-tuong-lai",
            author=self.author,
            content="Chưa đến ngày công bố.",
            status=StatusChoices.PUBLISHED,
            published_at=timezone.now() + timedelta(days=5),
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

    def test_article_list_view_200(self):
        """Trang danh sách bài viết trả về HTTP 200 và chỉ hiển thị bài đã xuất bản"""
        response = self.client.get(reverse("content:article_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/article_list.html")
        self.assertContains(response, "Đánh giá bàn phím E-Dra EK387")
        # Không được hiển thị bài nháp và bài hẹn giờ tương lai
        self.assertNotContains(response, "Bài viết nháp chưa công khai")
        self.assertNotContains(response, "Bài viết hẹn giờ tương lai")

    def test_article_list_filter_by_type(self):
        """Lọc bài viết theo loại (Review, Buying Guide...)"""
        response = self.client.get(reverse("content:article_list") + "?type=review")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Đánh giá bàn phím E-Dra EK387")

    def test_article_detail_view_published_200(self):
        """Trang chi tiết bài viết đã xuất bản hiển thị đầy đủ thông tin minh bạch"""
        response = self.client.get(reverse("content:article_detail", kwargs={"slug": self.article_published.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/article_detail.html")
        self.assertContains(response, "Đánh giá bàn phím E-Dra EK387")
        self.assertContains(response, "Thông tin minh bạch biên tập")
        self.assertContains(response, "Đã trực tiếp trải nghiệm")
        self.assertContains(response, "2 tuần")
        self.assertContains(response, "Công bố minh bạch")
        self.assertContains(response, "E-Dra")

    def test_article_detail_draft_returns_404(self):
        """Truy cập bài viết nháp qua URL trực tiếp bắt buộc trả về 404"""
        response = self.client.get(reverse("content:article_detail", kwargs={"slug": self.article_draft.slug}))
        self.assertEqual(response.status_code, 404)

    def test_article_detail_future_published_at_returns_404(self):
        """Truy cập bài viết có lịch xuất bản trong tương lai bắt buộc trả về 404"""
        response = self.client.get(reverse("content:article_detail", kwargs={"slug": self.article_future.slug}))
        self.assertEqual(response.status_code, 404)

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
        request.user = self.author

        readonly_fields = article_admin.get_readonly_fields(request, draft_article)
        self.assertIn("status", readonly_fields)
        self.assertIn("published_at", readonly_fields)
