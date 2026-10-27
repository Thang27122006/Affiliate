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


class SEOTechnicalTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="author1", first_name="Ban", last_name="Biên Tập", password="password")
        self.category = Category.objects.create(
            name="Chuột máy tính",
            slug="chuot-may-tinh",
            status=StatusChoices.PUBLISHED,
        )
        self.draft_category = Category.objects.create(
            name="Bàn phím cơ nháp",
            slug="ban-phim-co-nhap",
            status=StatusChoices.DRAFT,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Logitech Pebble M350",
            brand="Logitech",
            slug="logitech-pebble-m350",
            status=StatusChoices.PUBLISHED,
        )
        self.draft_product = Product.objects.create(
            category=self.category,
            name="Sản phẩm nháp nội bộ",
            brand="BrandX",
            slug="san-pham-nhap-noi-bo",
            status=StatusChoices.DRAFT,
        )
        self.article = Article.objects.create(
            title="Đánh giá chi tiết Logitech Pebble M350",
            slug="danh-gia-chi-tiet-logitech-pebble-m350",
            summary="Đánh giá ưu nhược điểm chuột Logitech Pebble M350 cho sinh viên.",
            author=self.user,
            status=StatusChoices.PUBLISHED,
        )
        self.draft_article = Article.objects.create(
            title="Bài viết nháp chưa xuất bản",
            slug="bai-viet-nhap-chua-xuat-ban",
            author=self.user,
            status=StatusChoices.DRAFT,
        )

    def test_robots_txt(self):
        """robots.txt trả về định dạng text/plain, chặn đúng các path kỹ thuật và khai báo sitemap"""
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("User-agent: *", content)
        self.assertIn("Disallow: /admin/", content)
        self.assertIn("Disallow: /analytics/", content)
        self.assertIn("Disallow: /go/", content)
        self.assertIn("Disallow: /tim-kiem/", content)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", content)

    def test_sitemap_xml_contains_only_published_content(self):
        """sitemap.xml chỉ chứa trang công khai và nội dung đã published, không chứa bản nháp"""
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])
        content = response.content.decode("utf-8")

        # Phải chứa các trang tĩnh quan trọng
        self.assertIn("<loc>http://testserver/</loc>", content)
        self.assertIn("<loc>http://testserver/gioi-thieu/</loc>", content)
        self.assertIn("<loc>http://testserver/chinh-sach-rieng-tu/</loc>", content)
        self.assertIn("<loc>http://testserver/san-pham/</loc>", content)
        self.assertIn("<loc>http://testserver/bai-viet/</loc>", content)

        # Phải chứa nội dung đã xuất bản
        self.assertIn(f"<loc>http://testserver/danh-muc/{self.category.slug}/</loc>", content)
        self.assertIn(f"<loc>http://testserver/san-pham/{self.product.slug}/</loc>", content)
        self.assertIn(f"<loc>http://testserver/bai-viet/{self.article.slug}/</loc>", content)

        # TUYỆT ĐỐI KHÔNG chứa nội dung nháp
        self.assertNotIn(self.draft_category.slug, content)
        self.assertNotIn(self.draft_product.slug, content)
        self.assertNotIn(self.draft_article.slug, content)

        # Không chứa các URL kỹ thuật hoặc tìm kiếm
        self.assertNotIn("/tim-kiem/", content)
        self.assertNotIn("/admin/", content)
        self.assertNotIn("/go/", content)

    def test_canonical_urls_use_dynamic_domain(self):
        """Canonical URL sử dụng domain cấu hình từ request, không dùng domain giả định cố định"""
        # Trang chủ
        resp_home = self.client.get("/")
        self.assertContains(resp_home, '<link rel="canonical" href="http://testserver/">')

        # Chi tiết sản phẩm
        resp_prod = self.client.get(f"/san-pham/{self.product.slug}/")
        self.assertContains(resp_prod, f'<link rel="canonical" href="http://testserver/san-pham/{self.product.slug}/">')

        # Chi tiết bài viết
        resp_art = self.client.get(f"/bai-viet/{self.article.slug}/")
        self.assertContains(resp_art, f'<link rel="canonical" href="http://testserver/bai-viet/{self.article.slug}/">')

    def test_noindex_on_search_and_filters(self):
        """Trang tìm kiếm và tổ hợp lọc không có giá trị độc lập phải có noindex, follow"""
        # Tìm kiếm
        resp_search = self.client.get("/tim-kiem/?q=chuot")
        self.assertContains(resp_search, '<meta name="robots" content="noindex, follow">')

        # So sánh
        resp_compare = self.client.get(f"/so-sanh/?p={self.product.slug}")
        self.assertContains(resp_compare, '<meta name="robots" content="noindex, follow">')

        # Trang sản phẩm có query lọc
        resp_prod_filter = self.client.get("/san-pham/?brand=Logitech")
        self.assertContains(resp_prod_filter, '<meta name="robots" content="noindex, follow">')

        # Trang danh mục có query lọc
        resp_cat_filter = self.client.get(f"/danh-muc/{self.category.slug}/?brand=Logitech")
        self.assertContains(resp_cat_filter, '<meta name="robots" content="noindex, follow">')

        # Trang sản phẩm gốc (không lọc) cho phép index
        resp_prod_clean = self.client.get("/san-pham/")
        self.assertContains(resp_prod_clean, '<meta name="robots" content="index, follow">')

    def test_privacy_policy_content(self):
        """Trang chính sách quyền riêng tư mô tả trung thực hệ thống dữ liệu kỹ thuật"""
        response = self.client.get(reverse("core:privacy_policy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chính Sách Quyền Riêng Tư")
        # Khẳng định không lưu IP thô
        self.assertContains(response, "KHÔNG thu thập địa chỉ IP thô")
        # Khẳng định không fingerprinting
        self.assertContains(response, "KHÔNG thu thập vân tay trình duyệt")
        # Khẳng định không PII người mua
        self.assertContains(response, "KHÔNG chứa thông tin cá nhân của người mua")

    def test_editorial_transparency_and_correction_policy(self):
        """Trang giới thiệu chứa chính sách sửa thông tin sai và 3 mẫu biên tập chuẩn"""
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chính sách hiệu đính & Sửa thông tin sai")
        self.assertContains(response, "Mẫu 1: Bài Đánh Giá Chi Tiết")
        self.assertContains(response, "Mẫu 2: Bài So Sánh Đối Đầu")
        self.assertContains(response, "Mẫu 3: Cẩm Nang Hướng Dẫn Mua Sắm")
        self.assertContains(response, "Tuyệt đối không dùng AI để bịa đặt")

    def test_article_structured_data_and_open_graph(self):
        """Bài viết có Open Graph đầy đủ, Article & BreadcrumbList schema đúng sự thật, không có rating giả"""
        response = self.client.get(f"/bai-viet/{self.article.slug}/")
        self.assertEqual(response.status_code, 200)

        # Open Graph
        self.assertContains(response, '<meta property="og:type" content="article">')
        self.assertContains(response, f'<meta property="og:title" content="{self.article.title} - Góc Phụ Kiện">')

        # Structured Data JSON-LD
        self.assertContains(response, '"@type": "Article"')
        self.assertContains(response, '"@type": "BreadcrumbList"')
        self.assertContains(response, f'"headline": "{self.article.title}"')

        # TUYỆT ĐỐI KHÔNG chứa rating, aggregateRating giả
        self.assertNotContains(response, '"aggregateRating"')
        self.assertNotContains(response, '"ratingValue"')

    def test_product_detail_structured_data_no_fake_schemas(self):
        """Trang chi tiết sản phẩm chỉ có BreadcrumbList, CHƯA thêm Product/Offer schema và KHÔNG tạo rating giả"""
        response = self.client.get(f"/san-pham/{self.product.slug}/")
        self.assertEqual(response.status_code, 200)

        # Có BreadcrumbList
        self.assertContains(response, '"@type": "BreadcrumbList"')

        # Chưa thêm Product schema khi chưa có dữ liệu thời gian thực
        self.assertNotContains(response, '"@type": "Product"')
        self.assertNotContains(response, '"aggregateRating"')
        self.assertNotContains(response, '"ratingValue"')

