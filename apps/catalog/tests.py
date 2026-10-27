from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from apps.catalog.models import (
    Category,
    Product,
    SpecificationDefinition,
    ProductSpecification,
    StatusChoices,
    DataTypeChoices,
)


class CatalogConstraintsAndViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat_mouse = Category.objects.create(
            name="Chuột máy tính",
            slug="chuot-may-tinh",
            status=StatusChoices.PUBLISHED,
        )
        self.cat_keyboard = Category.objects.create(
            name="Bàn phím",
            slug="ban-phim",
            status=StatusChoices.PUBLISHED,
        )
        self.cat_draft = Category.objects.create(
            name="Danh mục nháp",
            slug="danh-muc-nhap",
            status=StatusChoices.DRAFT,
        )
        self.spec_dpi = SpecificationDefinition.objects.create(
            category=self.cat_mouse,
            name="Độ phân giải",
            key="dpi",
            data_type=DataTypeChoices.NUMBER,
        )
        self.spec_switch = SpecificationDefinition.objects.create(
            category=self.cat_keyboard,
            name="Loại switch",
            key="switch",
            data_type=DataTypeChoices.TEXT,
        )
        self.product_mouse = Product.objects.create(
            category=self.cat_mouse,
            name="G102",
            brand="Logitech",
            slug="logitech-g102",
            status=StatusChoices.PUBLISHED,
        )
        self.product_draft = Product.objects.create(
            category=self.cat_mouse,
            name="Chuột Nháp",
            brand="OEM",
            slug="oem-chuot-nhap",
            status=StatusChoices.DRAFT,
        )

    def test_unique_slug_generation(self):
        """Kiểm tra việc tự động xử lý xung đột slug khi trùng lặp"""
        p2 = Product(
            category=self.cat_mouse,
            name="G102",
            brand="Logitech",
        )
        p2.save()
        self.assertNotEqual(p2.slug, self.product_mouse.slug)
        self.assertTrue(p2.slug.startswith("logitech-g102-"))

    def test_cross_category_specification_rejected(self):
        """Thông số phải thuộc đúng danh mục của sản phẩm. Gán sai danh mục bắt buộc ném ValidationError"""
        invalid_spec = ProductSpecification(
            product=self.product_mouse,
            specification_definition=self.spec_switch,
            value="Blue Switch",
        )
        with self.assertRaises(ValidationError) as ctx:
            invalid_spec.full_clean()
        self.assertIn("specification_definition", ctx.exception.message_dict)

    def test_valid_category_specification_accepted(self):
        """Gán thông số đúng danh mục phải lưu thành công"""
        valid_spec = ProductSpecification(
            product=self.product_mouse,
            specification_definition=self.spec_dpi,
            value="8000",
        )
        valid_spec.full_clean()
        valid_spec.save()
        self.assertEqual(ProductSpecification.objects.count(), 1)

    def test_duplicate_specification_per_product_rejected(self):
        """Mỗi sản phẩm chỉ có duy nhất một giá trị cho mỗi định nghĩa thông số"""
        ProductSpecification.objects.create(
            product=self.product_mouse,
            specification_definition=self.spec_dpi,
            value="8000",
        )
        duplicate_spec = ProductSpecification(
            product=self.product_mouse,
            specification_definition=self.spec_dpi,
            value="6400",
        )
        with self.assertRaises(IntegrityError):
            duplicate_spec.save()

    def test_category_detail_view_published_200(self):
        """Trang chi tiết danh mục đã xuất bản trả về HTTP 200"""
        response = self.client.get(reverse("catalog:category_detail", kwargs={"slug": "chuot-may-tinh"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/category_detail.html")
        self.assertContains(response, "G102")
        # Không được chứa sản phẩm nháp
        self.assertNotContains(response, "Chuột Nháp")

    def test_category_detail_view_draft_returns_404(self):
        """Truy cập danh mục ở trạng thái nháp phải trả về 404 Not Found"""
        response = self.client.get(reverse("catalog:category_detail", kwargs={"slug": "danh-muc-nhap"}))
        self.assertEqual(response.status_code, 404)

    def test_product_detail_view_published_200(self):
        """Trang chi tiết sản phẩm đã xuất bản trả về HTTP 200"""
        response = self.client.get(reverse("catalog:product_detail", kwargs={"slug": "logitech-g102"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/product_detail.html")
        self.assertContains(response, "Logitech")
        self.assertContains(response, "G102")

    def test_product_detail_view_draft_returns_404(self):
        """Truy cập sản phẩm ở trạng thái nháp trực tiếp qua URL phải trả về 404 Not Found"""
        response = self.client.get(reverse("catalog:product_detail", kwargs={"slug": "oem-chuot-nhap"}))
        self.assertEqual(response.status_code, 404)

    def test_product_list_view_200(self):
        """Trang Tất cả sản phẩm trả về HTTP 200 và hiển thị sản phẩm đã xuất bản"""
        response = self.client.get(reverse("catalog:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/product_list.html")
        self.assertContains(response, "Logitech")
        self.assertContains(response, "G102")
        self.assertNotContains(response, "Chuột Nháp")

    def test_navigation_menu_structure_and_order(self):
        """Menu chính phải có đúng 4 mục theo thứ tự: Trang chủ, Bài viết, Phương pháp, Sản phẩm"""
        response = self.client.get(reverse("core:home"))
        content = response.content.decode("utf-8")

        # Kiểm tra sự xuất hiện và thứ tự của 4 mục chính
        pos_home = content.find("Trang chủ</a>")
        pos_articles = content.find("Bài viết</a>")
        pos_about = content.find("Phương pháp</a>")
        pos_products = content.find("<span>Sản phẩm</span>")

        self.assertTrue(pos_home != -1 and pos_articles != -1 and pos_about != -1 and pos_products != -1)
        self.assertTrue(pos_home < pos_articles < pos_about < pos_products)

        # Kiểm tra Chuột và Bàn phím không còn nằm ở menu cấp 1
        # Mà nằm bên trong dropdown của Sản phẩm
        self.assertContains(response, 'id="products-dropdown-menu"')
        self.assertContains(response, "Tất cả sản phẩm")
        self.assertContains(response, "Chuột máy tính")
        self.assertContains(response, "Bàn phím")
        # Danh mục nháp không được xuất hiện trong menu
        self.assertNotContains(response, "Danh mục nháp")

    def test_navigation_menu_active_states(self):
        """Kiểm tra active state đúng ngữ cảnh và không bị active Trang chủ trên các trang khác"""
        # 1. Trang chủ: Trang chủ active, các mục khác không
        res_home = self.client.get(reverse("core:home"))
        self.assertContains(res_home, 'class="nav-link active">Trang chủ</a>')

        # 2. Trang bài viết: Bài viết active, Trang chủ không
        res_articles = self.client.get(reverse("content:article_list"))
        self.assertNotContains(res_articles, 'class="nav-link active">Trang chủ</a>')
        self.assertContains(res_articles, 'class="nav-link active">Bài viết</a>')

        # 3. Trang phương pháp: Phương pháp active, Trang chủ không
        res_about = self.client.get(reverse("core:about"))
        self.assertNotContains(res_about, 'class="nav-link active">Trang chủ</a>')
        self.assertContains(res_about, 'class="nav-link active">Phương pháp</a>')

        # 4. Trang danh sách sản phẩm: Sản phẩm active, Trang chủ không
        res_prods = self.client.get(reverse("catalog:product_list"))
        self.assertNotContains(res_prods, 'class="nav-link active">Trang chủ</a>')
        self.assertContains(res_prods, 'nav-link nav-dropdown-btn active')

        # 5. Trang danh mục: Sản phẩm active và item danh mục con active
        res_cat = self.client.get(reverse("catalog:category_detail", kwargs={"slug": "chuot-may-tinh"}))
        self.assertNotContains(res_cat, 'class="nav-link active">Trang chủ</a>')
        self.assertContains(res_cat, 'nav-link nav-dropdown-btn active')
        self.assertContains(res_cat, 'dropdown-item active')
