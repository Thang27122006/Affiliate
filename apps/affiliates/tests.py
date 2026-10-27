from decimal import Decimal
from unittest.mock import patch
from urllib.parse import urlsplit
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.catalog.models import Category, Product, StatusChoices
from apps.affiliates.models import (
    Merchant,
    Offer,
    LinkModeChoices,
    OfferLinkModeChoices,
)
from apps.analytics.models import ClickEvent


class AffiliateLinkSafetyAndRedirectTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Chuột máy tính",
            slug="chuot-may-tinh",
            status=StatusChoices.PUBLISHED,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Chuột Logitech Pebble M350",
            brand="Logitech",
            slug="chuot-logitech-pebble-m350",
            status=StatusChoices.PUBLISHED,
        )
        self.merchant = Merchant.objects.create(
            name="Shopee Vietnam",
            slug="shopee-vn",
            website="https://shopee.vn",
            allowed_hostnames="shopee.vn, s.shopee.vn",
            link_mode=LinkModeChoices.DIRECT,
            is_active=True,
        )
        self.valid_affiliate_url = "https://s.shopee.vn/xyz123?utm_source=affiliate&aff_id=9999&sub_id=review_m350"
        self.offer = Offer.objects.create(
            product=self.product,
            merchant=self.merchant,
            affiliate_url=self.valid_affiliate_url,
            price=Decimal("350000"),
            is_active=True,
        )

    # -------------------------------------------------------------
    # 1. KIỂM THỬ AN TOÀN URL & RÀNG BUỘC
    # -------------------------------------------------------------
    def test_valid_https_url_accepted(self):
        """URL HTTPS hợp lệ với domain hoặc subdomain được cấp phép phải pass validation"""
        offer = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/product-abc",
            price=Decimal("120000"),
        )
        offer.full_clean()
        offer.save()
        self.assertIsNotNone(offer.id)

    def test_preserve_tracking_parameters(self):
        """Giữ nguyên 100% các tham số tracking của URL do quản trị viên nhập"""
        complex_url = (
            "https://shopee.vn/universal-link/product/123456"
            "?utm_source=gocphukien&utm_medium=affiliate&aff_id=AF8888&tracking_tag=student_workspace&utm_campaign=back2school"
        )
        offer = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url=complex_url,
            price=Decimal("450000"),
        )
        offer.full_clean()
        offer.save()
        self.assertEqual(offer.affiliate_url, complex_url)

    def test_reject_http_protocol(self):
        """Giao thức HTTP không bảo mật phải bị từ chối"""
        offer = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="http://shopee.vn/product-insecure",
            price=Decimal("100000"),
        )
        with self.assertRaises(ValidationError) as ctx:
            offer.full_clean()
        self.assertIn("affiliate_url", ctx.exception.message_dict)
        self.assertIn("HTTPS", str(ctx.exception.message_dict["affiliate_url"]))

    def test_reject_dangerous_schemes(self):
        """Chặn triệt để các giao thức nguy hiểm: javascript:, data:, file:"""
        dangerous_urls = [
            "javascript:alert(document.cookie)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "ftp://shopee.vn/file",
        ]
        for url in dangerous_urls:
            with self.subTest(url=url):
                offer = Offer(
                    product=self.product,
                    merchant=self.merchant,
                    affiliate_url=url,
                    price=Decimal("100000"),
                )
                with self.assertRaises(ValidationError) as ctx:
                    offer.full_clean()
                self.assertIn("affiliate_url", ctx.exception.message_dict)

    def test_reject_credentials_in_url(self):
        """Chặn URL có chứa thông tin đăng nhập (username:password@hostname)"""
        credential_urls = [
            "https://admin:password@shopee.vn/product",
            "https://user@shopee.vn/path",
        ]
        for url in credential_urls:
            with self.subTest(url=url):
                offer = Offer(
                    product=self.product,
                    merchant=self.merchant,
                    affiliate_url=url,
                    price=Decimal("100000"),
                )
                with self.assertRaises(ValidationError) as ctx:
                    offer.full_clean()
                self.assertIn("affiliate_url", ctx.exception.message_dict)

    def test_reject_spoofed_hostnames(self):
        """Chặn các hostname mạo danh (dùng kết thúc giả mạo hoặc chứa chuỗi con)"""
        spoofed_urls = [
            "https://shopee.vn.evil-domain.com/phishing",
            "https://evil-shopee.vn/scam",
            "https://shopee.vn.attacker.org/steal",
            "https://notshopee.vn/deal",
        ]
        for url in spoofed_urls:
            with self.subTest(url=url):
                offer = Offer(
                    product=self.product,
                    merchant=self.merchant,
                    affiliate_url=url,
                    price=Decimal("100000"),
                )
                with self.assertRaises(ValidationError) as ctx:
                    offer.full_clean()
                self.assertIn("affiliate_url", ctx.exception.message_dict)

    def test_price_validation(self):
        """Giá bán phải dương (> 0) hoặc để trống (None)"""
        # Không được bằng 0
        offer_zero = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url=self.valid_affiliate_url,
            price=Decimal("0"),
        )
        with self.assertRaises(ValidationError):
            offer_zero.full_clean()

        # Không được âm
        offer_neg = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url=self.valid_affiliate_url,
            price=Decimal("-1000"),
        )
        with self.assertRaises(ValidationError):
            offer_neg.full_clean()

        # Được phép None
        offer_none = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url=self.valid_affiliate_url,
            price=None,
        )
        offer_none.full_clean()
        offer_none.save()
        self.assertIsNone(offer_none.price)

    # -------------------------------------------------------------
    # 2. KIỂM THỬ CHẾ ĐỘ LIÊN KẾT (LINK MODES)
    # -------------------------------------------------------------
    def test_default_link_mode_is_direct(self):
        """Mặc định khi chưa xác minh điều khoản, chế độ liên kết phải là 'direct'"""
        new_merchant = Merchant.objects.create(
            name="Lazada Vietnam",
            slug="lazada-vn",
            website="https://lazada.vn",
            allowed_hostnames="lazada.vn, s.lazada.vn",
        )
        self.assertEqual(new_merchant.link_mode, LinkModeChoices.DIRECT)

        new_offer = Offer.objects.create(
            product=self.product,
            merchant=new_merchant,
            affiliate_url="https://s.lazada.vn/deal123",
            price=Decimal("200000"),
        )
        self.assertEqual(new_offer.link_mode, OfferLinkModeChoices.USE_MERCHANT)
        self.assertEqual(new_offer.get_effective_link_mode(), LinkModeChoices.DIRECT)
        self.assertEqual(new_offer.get_destination_url(), "https://s.lazada.vn/deal123")

    def test_merchant_redirect_mode(self):
        """Khi Merchant được cấu hình redirect, Offer kế thừa chế độ redirect"""
        redirect_merchant = Merchant.objects.create(
            name="Tiki Vietnam",
            slug="tiki-vn",
            website="https://tiki.vn",
            allowed_hostnames="tiki.vn",
            link_mode=LinkModeChoices.REDIRECT,
        )
        offer = Offer.objects.create(
            product=self.product,
            merchant=redirect_merchant,
            affiliate_url="https://tiki.vn/product-p12345",
            price=Decimal("300000"),
        )
        self.assertEqual(offer.get_effective_link_mode(), LinkModeChoices.REDIRECT)
        expected_url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": offer.id})
        self.assertEqual(offer.get_destination_url(), expected_url)

    def test_offer_can_override_merchant_mode(self):
        """Offer có thể ghi đè chế độ liên kết của Merchant"""
        # Merchant là Direct nhưng Offer ghi đè Redirect
        self.offer.link_mode = OfferLinkModeChoices.REDIRECT
        self.offer.save()
        self.assertEqual(self.offer.get_effective_link_mode(), LinkModeChoices.REDIRECT)
        self.assertIn(f"/go/{self.offer.id}/", self.offer.get_destination_url())

        # Ngược lại: Merchant là Redirect nhưng Offer ghi đè Direct
        self.merchant.link_mode = LinkModeChoices.REDIRECT
        self.merchant.save()
        self.offer.link_mode = OfferLinkModeChoices.DIRECT
        self.offer.save()
        self.assertEqual(self.offer.get_effective_link_mode(), LinkModeChoices.DIRECT)
        self.assertEqual(self.offer.get_destination_url(), self.offer.affiliate_url)

    # -------------------------------------------------------------
    # 3. KIỂM THỬ CHUYỂN HƯỚNG NỘI BỘ (REDIRECT VIEW & SECURITY)
    # -------------------------------------------------------------
    def test_redirect_view_success(self):
        """Redirect thành công chuyển hướng HTTP 302 tới affiliate_url và ghi nhận ClickEvent"""
        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.offer.id})
        response = self.client.get(url, HTTP_REFERER="https://gocphukien.vn/san-pham/chuot-m350/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.valid_affiliate_url)

        # Kiểm tra ClickEvent được tạo trong database
        click = ClickEvent.objects.filter(offer=self.offer).first()
        self.assertIsNotNone(click)
        self.assertEqual(click.link_mode, LinkModeChoices.REDIRECT)
        self.assertEqual(click.referrer_path, "/san-pham/chuot-m350/")

    def test_redirect_view_nonexistent_offer(self):
        """Offer không tồn tại phải trả về 404"""
        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_view_inactive_offer(self):
        """Offer bị vô hiệu hóa (is_active=False) không được phép chuyển hướng (404)"""
        self.offer.is_active = False
        self.offer.save()

        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_view_inactive_merchant(self):
        """Merchant bị vô hiệu hóa (is_active=False) không được phép chuyển hướng (404)"""
        self.merchant.is_active = False
        self.merchant.save()

        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_view_draft_product(self):
        """Offer thuộc sản phẩm nháp (draft) không được phép chuyển hướng (404)"""
        self.product.status = StatusChoices.DRAFT
        self.product.save()

        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_view_draft_category(self):
        """Offer thuộc danh mục nháp (draft) không được phép chuyển hướng (404)"""
        self.category.status = StatusChoices.DRAFT
        self.category.save()

        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_open_redirect(self):
        """
        Chống Open Redirect: Không nhận URL đích tùy ý từ query parameters.
        Kẻ xấu truyền ?url=https://attacker.com hoặc ?next=... thì hệ thống vẫn
        chỉ chuyển hướng tới đúng URL database của Offer.
        """
        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.offer.id})
        malicious_query = f"{url}?url=https://evil.com&next=https://attacker.org&target=https://phishing.net"
        response = self.client.get(malicious_query)

        self.assertEqual(response.status_code, 302)
        # URL đích tuyệt đối vẫn là URL của Offer, không bị chiếm đoạt
        self.assertEqual(response.url, self.valid_affiliate_url)

    def test_redirect_resilience_when_logging_fails(self):
        """Nếu việc ghi nhận ClickEvent vào database gặp lỗi, redirect vẫn hoạt động bình thường"""
        url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.offer.id})

        with patch("apps.analytics.models.ClickEvent.objects.create", side_effect=Exception("Database error")):
            response = self.client.get(url)

        # Người đọc vẫn được chuyển hướng an toàn, không bị văng lỗi 500
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.valid_affiliate_url)
