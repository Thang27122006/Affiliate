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
        """Trang tìm kiếm khi chưa nhập từ khóa"""
        response = self.client.get(reverse("core:search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nhập từ khóa để tra cứu")

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
