from decimal import Decimal
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
from apps.affiliates.models import Merchant, Offer


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
            unit="DPI",
            data_type=DataTypeChoices.NUMBER,
            display_order=1,
        )
        self.spec_weight = SpecificationDefinition.objects.create(
            category=self.cat_mouse,
            name="Trọng lượng",
            key="weight",
            unit="g",
            data_type=DataTypeChoices.NUMBER,
            display_order=2,
        )
        self.spec_switch = SpecificationDefinition.objects.create(
            category=self.cat_keyboard,
            name="Loại switch",
            key="switch",
            data_type=DataTypeChoices.TEXT,
            display_order=1,
        )
        self.product_mouse = Product.objects.create(
            category=self.cat_mouse,
            name="G102 Lightsync",
            brand="Logitech",
            slug="logitech-g102",
            status=StatusChoices.PUBLISHED,
        )
        self.product_mouse2 = Product.objects.create(
            category=self.cat_mouse,
            name="M331 Silent",
            brand="Logitech",
            slug="logitech-m331",
            status=StatusChoices.PUBLISHED,
        )
        self.product_mouse3 = Product.objects.create(
            category=self.cat_mouse,
            name="EM901 Wireless",
            brand="DareU",
            slug="dareu-em901",
            status=StatusChoices.PUBLISHED,
        )
        self.product_keyboard = Product.objects.create(
            category=self.cat_keyboard,
            name="EK387 RGB",
            brand="E-Dra",
            slug="e-dra-ek387",
            status=StatusChoices.PUBLISHED,
        )
        self.product_no_price = Product.objects.create(
            category=self.cat_mouse,
            name="Chuột Chưa Có Giá",
            brand="OEM",
            slug="oem-chua-co-gia",
            status=StatusChoices.PUBLISHED,
        )
        self.product_draft = Product.objects.create(
            category=self.cat_mouse,
            name="Chuột Nháp",
            brand="OEM",
            slug="oem-chuot-nhap",
            status=StatusChoices.DRAFT,
        )

        # Nơi bán và offers
        self.merchant = Merchant.objects.create(
            name="Shopee",
            slug="shopee",
            website="https://shopee.vn",
            allowed_hostnames="shopee.vn",
            is_active=True,
        )
        # Offer cho G102 (350.000 đ)
        Offer.objects.create(
            product=self.product_mouse,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/demo-g102",
            price=Decimal("350000"),
            is_active=True,
        )
        # Offer cho M331 (320.000 đ)
        Offer.objects.create(
            product=self.product_mouse2,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/demo-m331",
            price=Decimal("320000"),
            is_active=True,
        )
        # Offer cho EM901 (800.000 đ)
        Offer.objects.create(
            product=self.product_mouse3,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/demo-em901",
            price=Decimal("800000"),
            is_active=True,
        )
        # Offer cho Keyboard (590.000 đ)
        Offer.objects.create(
            product=self.product_keyboard,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/demo-ek387",
            price=Decimal("590000"),
            is_active=True,
        )
        # Offer không có giá (price=None)
        Offer.objects.create(
            product=self.product_no_price,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/demo-no-price",
            price=None,
            is_active=True,
        )

        # Gán đầy đủ thông số cho M331
        ProductSpecification.objects.create(
            product=self.product_mouse2,
            specification_definition=self.spec_dpi,
            value="1000",
        )
        ProductSpecification.objects.create(
            product=self.product_mouse2,
            specification_definition=self.spec_weight,
            value="101",
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
        self.assertEqual(ProductSpecification.objects.filter(product=self.product_mouse).count(), 1)

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

    # =========================================================================
    # TESTS BỘ LỌC (FILTERING & SORTING)
    # =========================================================================

    def test_combined_filtering_category_brand_and_price(self):
        """Kiểm thử lọc kết hợp: Danh mục + Thương hiệu + Khoảng giá tham khảo"""
        # Lọc: Chuột máy tính, thương hiệu Logitech, khoảng giá 300k - 700k
        url = reverse("catalog:product_list") + "?category=chuot-may-tinh&brand=Logitech&price_range=300_700"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        products = list(response.context["page_obj"])
        product_slugs = [p.slug for p in products]

        # G102 (350k) và M331 (320k) thỏa mãn
        self.assertIn("logitech-g102", product_slugs)
        self.assertIn("logitech-m331", product_slugs)

        # EM901 (DareU, 800k) không thỏa thương hiệu và ngoài khoảng giá
        self.assertNotIn("dareu-em901", product_slugs)
        # EK387 (Bàn phím) không thỏa danh mục
        self.assertNotIn("e-dra-ek387", product_slugs)

    def test_missing_price_handling_not_zero(self):
        """
        Sản phẩm chưa có giá tham khảo được xử lý riêng biệt:
        - Không coi là 0 đồng.
        - Bị loại trừ khi lọc theo khoảng giá số học cụ thể.
        - Chỉ hiển thị khi lọc rõ ràng 'Chưa có giá' (price_range=no_price hoặc no_price=1).
        """
        # 1. Lọc khoảng giá dưới 300k: Sản phẩm chưa có giá không được lọt vào (không coi là 0đ)
        url_under_300 = reverse("catalog:product_list") + "?price_range=under_300"
        res_under = self.client.get(url_under_300)
        slugs_under = [p.slug for p in res_under.context["page_obj"]]
        self.assertNotIn("oem-chua-co-gia", slugs_under)

        # 2. Lọc riêng sản phẩm chưa có giá: Chỉ trả về sản phẩm không có giá
        url_no_price = reverse("catalog:product_list") + "?price_range=no_price"
        res_no_price = self.client.get(url_no_price)
        slugs_no_price = [p.slug for p in res_no_price.context["page_obj"]]
        self.assertIn("oem-chua-co-gia", slugs_no_price)
        self.assertNotIn("logitech-g102", slugs_no_price)

    def test_price_sorting_asc_and_desc_nulls_last(self):
        """
        Khi sắp xếp theo giá tham khảo (thấp đến cao và cao đến thấp),
        sản phẩm chưa có giá phải luôn được xếp cuối cùng (nulls_last),
        tuyệt đối không bị đưa lên đầu coi như 0đ.
        """
        # 1. Sắp xếp giá thấp đến cao: 320k (M331) -> 350k (G102) -> 590k (EK387) -> 800k (EM901) -> Chưa có giá
        res_asc = self.client.get(reverse("catalog:product_list") + "?sort=price_asc")
        products_asc = list(res_asc.context["page_obj"])
        slugs_asc = [p.slug for p in products_asc]

        # Vị trí đầu tiên phải là sản phẩm có giá thấp nhất (M331: 320k)
        self.assertEqual(slugs_asc[0], "logitech-m331")
        # Sản phẩm chưa có giá phải ở vị trí cuối cùng
        self.assertEqual(slugs_asc[-1], "oem-chua-co-gia")

        # 2. Sắp xếp giá cao đến thấp: 800k -> 590k -> 350k -> 320k -> Chưa có giá
        res_desc = self.client.get(reverse("catalog:product_list") + "?sort=price_desc")
        products_desc = list(res_desc.context["page_obj"])
        slugs_desc = [p.slug for p in products_desc]

        self.assertEqual(slugs_desc[0], "dareu-em901")
        # Sản phẩm chưa có giá vẫn phải ở vị trí cuối cùng
        self.assertEqual(slugs_desc[-1], "oem-chua-co-gia")

    def test_pagination_preserves_query_filters(self):
        """Phân trang phải bảo toàn toàn bộ query parameters bằng template tag url_replace"""
        url = reverse("catalog:product_list") + "?category=chuot-may-tinh&brand=Logitech&sort=price_asc"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_category"], "chuot-may-tinh")
        self.assertEqual(response.context["selected_brand"], "Logitech")
        self.assertEqual(response.context["current_sort"], "price_asc")

    # =========================================================================
    # TESTS SO SÁNH SẢN PHẨM (PRODUCT COMPARISON)
    # =========================================================================

    def test_compare_valid_two_and_three_products(self):
        """So sánh hợp lệ giữa 2 và 3 sản phẩm trong cùng danh mục"""
        # 1. So sánh 2 sản phẩm chuột
        url_2 = reverse("catalog:compare") + "?p=logitech-g102&p=logitech-m331"
        res_2 = self.client.get(url_2)
        self.assertEqual(res_2.status_code, 200)
        self.assertTemplateUsed(res_2, "catalog/compare.html")
        self.assertIsNone(res_2.context["error_message"])
        self.assertEqual(len(res_2.context["products"]), 2)
        self.assertContains(res_2, "G102 Lightsync")
        self.assertContains(res_2, "M331 Silent")

        # 2. So sánh 3 sản phẩm chuột
        url_3 = reverse("catalog:compare") + "?p=logitech-g102&p=logitech-m331&p=dareu-em901"
        res_3 = self.client.get(url_3)
        self.assertEqual(res_3.status_code, 200)
        self.assertEqual(len(res_3.context["products"]), 3)

    def test_compare_duplicate_products_rejected(self):
        """
        Không cho phép thêm trùng sản phẩm trong bảng so sánh.
        Nếu truyền 2 slug giống nhau, hệ thống tự lọc trùng và báo lỗi thiếu sản phẩm (< 2).
        """
        url = reverse("catalog:compare") + "?p=logitech-g102&p=logitech-g102"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["error_message"])
        self.assertIn("tối thiểu 2 sản phẩm", response.context["error_message"])

    def test_compare_exceed_max_quantity_rejected(self):
        """Truyền vượt quá số lượng tối đa (> 3 sản phẩm) phải báo lỗi từ chối"""
        url = reverse("catalog:compare") + "?p=logitech-g102&p=logitech-m331&p=dareu-em901&p=oem-chua-co-gia"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["error_message"])
        self.assertIn("tối đa 3 sản phẩm", response.context["error_message"])

    def test_compare_different_categories_rejected(self):
        """Chỉ cho phép so sánh các sản phẩm cùng danh mục; khác danh mục phải báo lỗi"""
        # G102 là Chuột, EK387 là Bàn phím
        url = reverse("catalog:compare") + "?p=logitech-g102&p=e-dra-ek387"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["error_message"])
        self.assertIn("cùng một danh mục", response.context["error_message"])

    def test_compare_excludes_draft_products(self):
        """Sản phẩm ở trạng thái nháp không được phép đưa vào bảng so sánh công khai"""
        # Truyền 1 sản phẩm xuất bản và 1 sản phẩm nháp
        url = reverse("catalog:compare") + "?p=logitech-g102&p=oem-chuot-nhap"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Sản phẩm nháp bị loại bỏ, chỉ còn 1 sản phẩm hợp lệ nên báo lỗi thiếu sản phẩm
        self.assertIsNotNone(response.context["error_message"])
        self.assertIn("tối thiểu 2 sản phẩm", response.context["error_message"])

    def test_compare_missing_specifications_displayed_as_chua_co_thong_tin(self):
        """
        Thuộc tính kỹ thuật chưa được nhập giá trị phải hiển thị là 'Chưa có thông tin'.
        G102 có DPI nhưng chưa gán Trọng lượng; M331 có cả 2.
        """
        # G102 chỉ có DPI, không có Trọng lượng
        ProductSpecification.objects.create(
            product=self.product_mouse,
            specification_definition=self.spec_dpi,
            value="8000",
        )
        url = reverse("catalog:compare") + "?p=logitech-g102&p=logitech-m331"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        spec_rows = response.context["spec_rows"]
        # Hàng 1: Độ phân giải DPI
        dpi_row = next(r for r in spec_rows if r["name"] == "Độ phân giải")
        self.assertEqual(dpi_row["values"][0]["display"], "8000 DPI")
        self.assertEqual(dpi_row["values"][1]["display"], "1000 DPI")

        # Hàng 2: Trọng lượng
        weight_row = next(r for r in spec_rows if r["name"] == "Trọng lượng")
        # G102 chưa có thông tin trọng lượng
        self.assertEqual(weight_row["values"][0]["display"], "Chưa có thông tin")
        self.assertFalse(weight_row["values"][0]["has_value"])
        # M331 có trọng lượng
        self.assertEqual(weight_row["values"][1]["display"], "101 g")
        self.assertTrue(weight_row["values"][1]["has_value"])

    def test_compare_spec_order_matches_category_definitions(self):
        """Thứ tự các hàng thông số kỹ thuật phải đúng theo display_order của danh mục chung"""
        url = reverse("catalog:compare") + "?p=logitech-g102&p=logitech-m331"
        response = self.client.get(url)
        spec_rows = response.context["spec_rows"]

        row_names = [r["name"] for r in spec_rows]
        # display_order 1: Độ phân giải, display_order 2: Trọng lượng
        self.assertEqual(row_names, ["Độ phân giải", "Trọng lượng"])
