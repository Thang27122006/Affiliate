from django.test import TestCase
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


class CatalogConstraintsTestCase(TestCase):
    def setUp(self):
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
        # Gán thông số 'Loại switch' (của Bàn phím) cho chuột Logitech G102
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

    def test_draft_status_not_in_published_queryset(self):
        """Bản ghi ở trạng thái nháp (draft) không được xuất hiện trong published manager"""
        draft_product = Product.objects.create(
            category=self.cat_mouse,
            name="Chuột Nháp",
            brand="OEM",
            status=StatusChoices.DRAFT,
        )
        published_products = Product.objects.published()
        self.assertIn(self.product_mouse, published_products)
        self.assertNotIn(draft_product, published_products)
