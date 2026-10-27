from django.test import TestCase, Client
from django.urls import reverse
from apps.catalog.models import Category, Product, StatusChoices
from apps.content.models import Article, ArticleTypeChoices
from django.contrib.auth import get_user_model

User = get_user_model()


class CoreViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(
            name="Chuột máy tính",
            slug="chuot-may-tinh",
            status=StatusChoices.PUBLISHED,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Pebble M350",
            brand="Logitech",
            slug="logitech-pebble-m350",
            status=StatusChoices.PUBLISHED,
        )
        self.article = Article.objects.create(
            title="Đánh giá chuột M350",
            slug="danh-gia-chuot-m350",
            author=self.user,
            status=StatusChoices.PUBLISHED,
        )

    def test_home_page_status_and_content(self):
        """Trang chủ hiển thị danh mục, sản phẩm và bài viết đã xuất bản"""
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertContains(response, "Chuột máy tính")
        self.assertContains(response, "Pebble M350")
        self.assertContains(response, "Đánh giá chuột M350")

    def test_about_page_status_and_content(self):
        """Trang giới thiệu & phương pháp hiển thị đầy đủ thông tin"""
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/about.html")
        self.assertContains(response, "Phương Pháp Đánh Giá")
        self.assertContains(response, "Chính sách tiếp thị liên kết")

    def test_search_page_with_results(self):
        """Trang tìm kiếm trả về đúng sản phẩm và bài viết"""
        response = self.client.get(reverse("core:search") + "?q=Logitech")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/search.html")
        self.assertContains(response, "Pebble M350")

    def test_search_page_empty_query(self):
        """Trang tìm kiếm khi chưa nhập từ khóa hoặc chỉ có khoảng trắng"""
        response = self.client.get(reverse("core:search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nhập từ khóa để tra cứu")

        # Chuỗi chỉ toàn khoảng trắng
        response_spaces = self.client.get(reverse("core:search") + "?q=   ")
        self.assertEqual(response_spaces.status_code, 200)
        self.assertEqual(response_spaces.context["query"], "")
        self.assertContains(response_spaces, "Nhập từ khóa để tra cứu")

    def test_search_case_insensitive(self):
        """Tìm kiếm không phân biệt hoa thường"""
        # Viết hoa
        res_upper = self.client.get(reverse("core:search") + "?q=LOGITECH")
        self.assertContains(res_upper, "Pebble M350")

        # Viết thường
        res_lower = self.client.get(reverse("core:search") + "?q=logitech")
        self.assertContains(res_lower, "Pebble M350")

    def test_search_unaccent_vietnamese(self):
        """
        Tìm kiếm tiếng Việt không dấu (unaccent) trên PostgreSQL.
        Từ khóa 'chuot' phải tìm thấy bài viết 'Đánh giá chuột M350'.
        """
        response = self.client.get(reverse("core:search") + "?q=chuot")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Đánh giá chuột M350")

    def test_search_excessive_length_truncated(self):
        """Từ khóa quá dài (>120 ký tự) được tự động cắt ngắn an toàn và hiển thị thông báo"""
        long_query = "a" * 150
        response = self.client.get(reverse("core:search") + f"?q={long_query}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["query"]), 120)
        self.assertContains(response, "Từ khóa tìm kiếm quá dài đã được tự động rút gọn")

    def test_search_excludes_draft_and_future_articles(self):
        """
        Tìm kiếm tuyệt đối không hiển thị sản phẩm bản nháp,
        bài viết bản nháp hoặc bài viết hẹn giờ trong tương lai.
        """
        from datetime import timedelta
        from django.utils import timezone

        # Tạo sản phẩm nháp
        Product.objects.create(
            category=self.category,
            name="Logitech Secret Draft",
            brand="Logitech",
            slug="logitech-secret-draft",
            status=StatusChoices.DRAFT,
        )

        # Tạo bài viết nháp
        Article.objects.create(
            title="Đánh giá bí mật Logitech",
            slug="danh-gia-bi-mat-logitech",
            author=self.user,
            status=StatusChoices.DRAFT,
        )

        # Tạo bài viết hẹn giờ tương lai
        Article.objects.create(
            title="Bài viết tương lai Logitech",
            slug="bai-viet-tuong-lai-logitech",
            author=self.user,
            status=StatusChoices.PUBLISHED,
            published_at=timezone.now() + timedelta(days=2),
        )

        response = self.client.get(reverse("core:search") + "?q=Logitech")
        self.assertContains(response, "Pebble M350")
        self.assertNotContains(response, "Logitech Secret Draft")
        self.assertNotContains(response, "Đánh giá bí mật Logitech")
        self.assertNotContains(response, "Bài viết tương lai Logitech")

    def test_search_splits_products_and_articles(self):
        """Kết quả tìm kiếm được chia tách rõ ràng thành sản phẩm và bài viết"""
        response = self.client.get(reverse("core:search") + "?q=M350")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["products"]), 1)
        self.assertEqual(len(response.context["articles"]), 1)
        self.assertContains(response, "Sản Phẩm Phù Hợp")
        self.assertContains(response, "Bài Viết & Đánh Giá Phù Hợp")

    def test_custom_404_page(self):
        """Đường dẫn không tồn tại trả về mã 404 và giao diện thân thiện"""
        response = self.client.get("/duong-dan-khong-ton-tai-12345/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Không tìm thấy trang bạn yêu cầu", status_code=404)

    def test_health_check_endpoint(self):
        """Endpoint health check vẫn hoạt động bình thường"""
        response = self.client.get(reverse("core:health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
