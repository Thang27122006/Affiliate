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
