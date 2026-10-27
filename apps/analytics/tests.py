import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from apps.catalog.models import Category, Product, StatusChoices
from apps.affiliates.models import Merchant, Offer, LinkModeChoices
from apps.analytics.models import ClickEvent


class AnalyticsClickTrackingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        cache.clear()

        self.category = Category.objects.create(
            name="Bàn phím cơ",
            slug="ban-phim-co",
            status=StatusChoices.PUBLISHED,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Bàn phím Keychron K2",
            brand="Keychron",
            slug="ban-phim-keychron-k2",
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
        self.offer = Offer.objects.create(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://s.shopee.vn/keychron-k2?aff_id=12345",
            price=Decimal("1790000"),
            is_active=True,
        )

    def tearDown(self):
        cache.clear()

    # -------------------------------------------------------------
    # 1. API GHI NHẬN LƯỢT BẤM LIÊN KẾT TRỰC TIẾP (DIRECT CLICKS)
    # -------------------------------------------------------------
    def test_track_direct_click_success(self):
        """API ghi nhận lượt bấm trực tiếp thành công và lưu đúng thông tin"""
        url = reverse("analytics:track_click_api")
        payload = {
            "offer_id": self.offer.id,
            "referrer_path": "/san-pham/ban-phim-keychron-k2/?filter=top",
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")

        # Kiểm tra bản ghi trong database
        click = ClickEvent.objects.filter(offer=self.offer).first()
        self.assertIsNotNone(click)
        self.assertEqual(click.link_mode, LinkModeChoices.DIRECT)
        # Đường dẫn nguồn đã được làm sạch, loại bỏ query param nhạy cảm
        self.assertEqual(click.referrer_path, "/san-pham/ban-phim-keychron-k2/")

    def test_track_click_privacy_no_raw_ip_or_fingerprint(self):
        """Đảm bảo model ClickEvent không thu thập IP thô, fingerprint hay PII"""
        field_names = [f.name for f in ClickEvent._meta.get_fields()]
        self.assertNotIn("ip", field_names)
        self.assertNotIn("ip_address", field_names)
        self.assertNotIn("fingerprint", field_names)
        self.assertNotIn("user_agent", field_names)
        self.assertNotIn("cookies", field_names)

    def test_track_click_debounce_throttle(self):
        """Hạn chế gửi sự kiện lặp tức thời (Debounce trong 3 giây)"""
        url = reverse("analytics:track_click_api")
        payload = {"offer_id": self.offer.id, "referrer_path": "/san-pham/ban-phim-keychron-k2/"}

        # Lần 1: Thành công
        res1 = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json().get("status"), "ok")

        # Lần 2 ngay tức thì từ cùng session: Bị chặn spam lặp
        res2 = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json().get("status"), "ignored")
        self.assertEqual(res2.json().get("reason"), "throttled")

        # Chỉ có đúng 1 bản ghi trong database
        self.assertEqual(ClickEvent.objects.filter(offer=self.offer).count(), 1)

    def test_track_click_invalid_inputs(self):
        """Kiểm tra xử lý lỗi khi thiếu hoặc sai tham số offer_id"""
        url = reverse("analytics:track_click_api")

        # Không truyền offer_id
        res_missing = self.client.post(url, data=json.dumps({}), content_type="application/json")
        self.assertEqual(res_missing.status_code, 400)

        # offer_id không phải số
        res_invalid_type = self.client.post(url, data=json.dumps({"offer_id": "abc"}), content_type="application/json")
        self.assertEqual(res_invalid_type.status_code, 400)

        # offer_id không tồn tại
        res_not_found = self.client.post(url, data=json.dumps({"offer_id": 999999}), content_type="application/json")
        self.assertEqual(res_not_found.status_code, 404)

    def test_track_click_inactive_offer_or_draft_product(self):
        """Không ghi nhận lượt bấm cho Offer ngừng hoạt động hoặc sản phẩm nháp"""
        url = reverse("analytics:track_click_api")

        # Offer inactive
        self.offer.is_active = False
        self.offer.save()
        res_inactive = self.client.post(url, data=json.dumps({"offer_id": self.offer.id}), content_type="application/json")
        self.assertEqual(res_inactive.status_code, 400)

        # Khôi phục offer nhưng sản phẩm nháp
        self.offer.is_active = True
        self.offer.save()
        self.product.status = StatusChoices.DRAFT
        self.product.save()
        res_draft = self.client.post(url, data=json.dumps({"offer_id": self.offer.id}), content_type="application/json")
        self.assertEqual(res_draft.status_code, 400)

    # -------------------------------------------------------------
    # 2. KIỂM THỬ KHẢ NĂNG CHỊU LỖI CỦA GIAO DIỆN KHI JS TẮT HOẶC TRACKING LỖI
    # -------------------------------------------------------------
    def test_direct_link_remains_functional_when_tracking_fails_or_js_disabled(self):
        """
        Với liên kết trực tiếp, thẻ <a> trong HTML luôn mang href là URL thật.
        Điều này đảm bảo khi người dùng tắt JavaScript hoặc API tracking bị lỗi/adblock chặn,
        người đọc vẫn mở được tab tới nơi bán mà không gặp bất kỳ trở ngại nào.
        """
        detail_url = reverse("catalog:product_detail", kwargs={"slug": self.product.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode("utf-8")

        # 1. URL thật phải xuất hiện trong thuộc tính href
        self.assertIn(f'href="{self.offer.affiliate_url}"', html)

        # 2. Phải có rel="noopener noreferrer sponsored" và target="_blank"
        self.assertIn('rel="noopener noreferrer sponsored"', html)
        self.assertIn('target="_blank"', html)

        # 3. Nút nơi bán phải có data attributes phục vụ tracking nhẹ
        self.assertIn('data-track-click="true"', html)
        self.assertIn(f'data-offer-id="{self.offer.id}"', html)
        self.assertIn('data-link-mode="direct"', html)

        # 4. Minh bạch hoa hồng tiếp thị phải xuất hiện trên trang
        self.assertIn("Minh bạch tài trợ", html)
        self.assertIn("hoa hồng nhỏ", html)
