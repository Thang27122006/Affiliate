import json
import io
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.catalog.models import Category, Product, StatusChoices
from apps.content.models import Article, ArticleTypeChoices
from apps.affiliates.models import Merchant, Offer, LinkModeChoices
from apps.analytics.models import (
    ClickEvent,
    PageView,
    AffiliateConversion,
    ConversionStatusChoices,
)
from apps.analytics.reconciliation import parse_reconciliation_csv

User = get_user_model()
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class AnalyticsFullTestSuite(TestCase):
    def setUp(self):
        self.client = Client()
        cache.clear()

        # Tạo người dùng: 1 staff và 1 normal user
        self.staff_user = User.objects.create_user(
            username="admin_staff",
            email="admin@gocphukien.vn",
            password="password123",
            is_staff=True,
        )
        self.normal_user = User.objects.create_user(
            username="reader_user",
            email="reader@example.com",
            password="password123",
            is_staff=False,
        )

        # Dữ liệu Catalog & Content mẫu
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
        self.article = Article.objects.create(
            title="Đánh giá chi tiết bàn phím cơ Keychron K2",
            slug="danh-gia-keychron-k2",
            article_type=ArticleTypeChoices.REVIEW,
            summary="Bàn phím cơ di động hoàn hảo cho sinh viên.",
            content="Nội dung đánh giá chi tiết...",
            author=self.staff_user,
            status=StatusChoices.PUBLISHED,
            published_at=timezone.now() - timedelta(days=5),
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
    # 1. KIỂM THỬ QUYỀN TRUY CẬP (STAFF PERMISSIONS)
    # -------------------------------------------------------------
    def test_anonymous_access_dashboard_redirects_to_login(self):
        """Khách vãng lai truy cập Dashboard bị chuyển hướng đến trang đăng nhập admin"""
        url = reverse("analytics:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_normal_user_access_dashboard_denied(self):
        """Người dùng thông thường (không phải staff) truy cập Dashboard bị từ chối"""
        self.client.login(username="reader_user", password="password123")
        url = reverse("analytics:dashboard")
        response = self.client.get(url)
        # @staff_member_required chuyển hướng người dùng không phải staff sang trang login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_staff_user_can_access_dashboard(self):
        """Tài khoản Staff có quyền truy cập đầy đủ vào trang Dashboard"""
        self.client.login(username="admin_staff", password="password123")
        url = reverse("analytics:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Báo Cáo Hiệu Quả & Đối Soát Tiếp Thị Liên Kết")
        self.assertContains(response, "Asia/Ho_Chi_Minh")

    def test_reconciliation_import_view_permissions(self):
        """Trang nhập CSV đối soát chỉ cho phép staff truy cập"""
        url = reverse("analytics:reconciliation_import")

        # Chưa đăng nhập -> 302
        response_anon = self.client.get(url)
        self.assertEqual(response_anon.status_code, 302)

        # Đăng nhập staff -> 200
        self.client.login(username="admin_staff", password="password123")
        response_staff = self.client.get(url)
        self.assertEqual(response_staff.status_code, 200)
        self.assertContains(response_staff, "Nhập Báo Cáo Đối Soát Hoa Hồng (CSV)")

    # -------------------------------------------------------------
    # 2. KIỂM THỬ GHI NHẬN PAGEVIEW & TÍNH CHỊU LỖI (RESILIENCE)
    # -------------------------------------------------------------
    def test_product_detail_records_pageview(self):
        """Khi xem chi tiết sản phẩm, một bản ghi PageView được tạo an toàn"""
        initial_count = PageView.objects.count()
        detail_url = reverse("catalog:product_detail", kwargs={"slug": self.product.slug})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageView.objects.count(), initial_count + 1)
        pv = PageView.objects.filter(product=self.product).first()
        self.assertIsNotNone(pv)
        self.assertEqual(pv.path, detail_url)

    def test_article_detail_records_pageview(self):
        """Khi xem chi tiết bài viết, một bản ghi PageView bài viết được tạo"""
        initial_count = PageView.objects.count()
        art_url = reverse("content:article_detail", kwargs={"slug": self.article.slug})
        response = self.client.get(art_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageView.objects.count(), initial_count + 1)
        pv = PageView.objects.filter(article=self.article).first()
        self.assertIsNotNone(pv)
        self.assertEqual(pv.path, art_url)

    def test_pageview_recording_failure_does_not_break_page(self):
        """Lỗi ghi nhận PageView không được làm gián đoạn việc hiển thị trang sản phẩm"""
        detail_url = reverse("catalog:product_detail", kwargs={"slug": self.product.slug})
        with patch("apps.analytics.models.PageView.objects.create", side_effect=Exception("DB Error")):
            response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    # -------------------------------------------------------------
    # 3. KIỂM THỬ TỶ LỆ CTR SỰ KIỆN & CHỐNG CHIA CHO 0
    # -------------------------------------------------------------
    def test_ctr_calculation_and_division_by_zero_prevention(self):
        """Kiểm tra tính toán CTR theo sự kiện và chống lỗi chia cho 0 khi views = 0"""
        self.client.login(username="admin_staff", password="password123")
        url = reverse("analytics:dashboard")

        # Khi chưa có views nào trong database -> CTR trả về None, hiển thị chữ 'Chưa có lượt xem'
        PageView.objects.all().delete()
        ClickEvent.objects.all().delete()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["overall_event_ctr"])
        self.assertContains(response, "Chưa có lượt xem")

        # Khi có 10 views và 2 clicks -> CTR = 20.0%
        for _ in range(10):
            PageView.objects.create(product=self.product, path="/san-pham/test/")
        for _ in range(2):
            ClickEvent.objects.create(offer=self.offer, link_mode="direct")

        response_with_data = self.client.get(url)
        self.assertEqual(response_with_data.status_code, 200)
        self.assertAlmostEqual(response_with_data.context["overall_event_ctr"], 20.0, places=1)
        # Chấp nhận cả định dạng dấu phẩy tiếng Việt (20,00%) hoặc dấu chấm (20.00%)
        html_content = response_with_data.content.decode("utf-8")
        self.assertTrue("20,00%" in html_content or "20.00%" in html_content)


    # -------------------------------------------------------------
    # 4. KIỂM THỬ BỘ LỌC KHOẢNG NGÀY & MÚI GIỜ ASIA/HO_CHI_MINH
    # -------------------------------------------------------------
    def test_date_range_filtering_with_vietnam_timezone(self):
        """Bộ lọc khoảng ngày chỉ tính các sự kiện trong khoảng, loại bỏ sự kiện ngoài khoảng"""
        self.client.login(username="admin_staff", password="password123")
        now_vn = datetime.now(VIETNAM_TZ)

        # 1. Sự kiện ngày hôm nay
        pv_today = PageView.objects.create(product=self.product, path="/today/")

        # 2. Sự kiện 45 ngày trước (ngoài khoảng 10 ngày)
        old_time = timezone.now() - timedelta(days=45)
        pv_old = PageView.objects.create(product=self.product, path="/old/")
        PageView.objects.filter(id=pv_old.id).update(created_at=old_time)

        # Lọc 7 ngày qua
        start_str = (now_vn - timedelta(days=7)).strftime("%Y-%m-%d")
        end_str = now_vn.strftime("%Y-%m-%d")

        url = f"{reverse('analytics:dashboard')}?start_date={start_str}&end_date={end_str}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Chỉ có 1 pageview được tính (hôm nay), loại bỏ pageview 45 ngày trước
        self.assertEqual(response.context["product_views_count"], 1)

    def test_inverted_date_range_swapped_safely(self):
        """Nếu start_date > end_date, hệ thống tự động hoán đổi an toàn không văng lỗi"""
        self.client.login(username="admin_staff", password="password123")
        url = f"{reverse('analytics:dashboard')}?start_date=2026-10-30&end_date=2026-10-01"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["start_date"], "2026-10-01")
        self.assertEqual(response.context["end_date"], "2026-10-30")

    # -------------------------------------------------------------
    # 5. KIỂM THỬ NHẬP CSV ĐỐI SOÁT (RECONCILIATION IMPORT)
    # -------------------------------------------------------------
    def test_reconciliation_csv_import_success(self):
        """Nhập file CSV hợp lệ tạo đúng các bản ghi AffiliateConversion"""
        csv_data = (
            "program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code\n"
            "Shopee Vietnam,ORDER_101,ITEM_1,2026-10-25 10:00:00,approved,15000,VND,prod-ban-phim-keychron-k2\n"
            "Shopee Vietnam,ORDER_101,ITEM_2,2026-10-25 10:00:00,approved,25000,VND,\n"
            "Tiki,TK_999,,2026-10-26 14:00:00,pending,30000,VND,art-danh-gia-keychron-k2\n"
            "Lazada,LAZ_888,L1,2026-10-27 15:30:00,approved,5.50,USD,\n"
        )
        result = parse_reconciliation_csv(csv_data)

        self.assertTrue(result["success"])
        self.assertEqual(result["total_rows"], 4)
        self.assertEqual(result["created_count"], 4)
        self.assertEqual(result["updated_count"], 0)
        self.assertEqual(AffiliateConversion.objects.count(), 4)

        # Kiểm tra đối chiếu sản phẩm & bài viết qua tracking_code
        item1 = AffiliateConversion.objects.get(external_transaction_id="ORDER_101", external_order_item_id="ITEM_1")
        self.assertEqual(item1.matched_product, self.product)
        self.assertEqual(item1.commission_amount, Decimal("15000"))

        item_tiki = AffiliateConversion.objects.get(external_transaction_id="TK_999")
        self.assertEqual(item_tiki.matched_article, self.article)

    def test_reconciliation_import_idempotent_no_duplicate_data(self):
        """Import lặp lại cùng một file không nhân đôi số lượng bản ghi hoặc doanh thu"""
        csv_data = (
            "program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code\n"
            "Shopee Vietnam,SPX_001,IT_1,2026-10-25 10:00:00,approved,50000,VND,\n"
        )
        # Lần 1: Tạo mới 1 bản ghi
        res1 = parse_reconciliation_csv(csv_data)
        self.assertEqual(res1["created_count"], 1)
        self.assertEqual(AffiliateConversion.objects.count(), 1)

        # Lần 2 với cùng file: Không tạo mới, updated_count = 1, DB vẫn chỉ có đúng 1 bản ghi
        res2 = parse_reconciliation_csv(csv_data)
        self.assertEqual(res2["created_count"], 0)
        self.assertEqual(res2["updated_count"], 1)
        self.assertEqual(AffiliateConversion.objects.count(), 1)

    def test_reconciliation_import_updates_status(self):
        """Import file mới cập nhật trạng thái từ pending sang approved chính xác"""
        csv_pending = (
            "program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code\n"
            "Shopee Vietnam,SPX_999,IT_1,2026-10-25 10:00:00,pending,40000,VND,\n"
        )
        parse_reconciliation_csv(csv_pending)
        record = AffiliateConversion.objects.get(external_transaction_id="SPX_999")
        self.assertEqual(record.status, ConversionStatusChoices.PENDING)

        # File tiếp theo sàn phê duyệt đơn hàng: status='approved'
        csv_approved = (
            "program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code\n"
            "Shopee Vietnam,SPX_999,IT_1,2026-10-25 10:00:00,approved,40000,VND,\n"
        )
        parse_reconciliation_csv(csv_approved)
        record.refresh_from_db()
        self.assertEqual(record.status, ConversionStatusChoices.APPROVED)

    def test_reconciliation_multi_item_order_distinct_records(self):
        """Nhiều sản phẩm trong cùng một mã đơn (cùng transaction_id, khác item_id) được lưu riêng biệt"""
        csv_multi = (
            "program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code\n"
            "Shopee Vietnam,ORDER_COMBO,ITEM_MOUSE,2026-10-25 10:00:00,approved,10000,VND,\n"
            "Shopee Vietnam,ORDER_COMBO,ITEM_KEYBOARD,2026-10-25 10:00:00,approved,30000,VND,\n"
        )
        result = parse_reconciliation_csv(csv_multi)
        self.assertTrue(result["success"])
        self.assertEqual(AffiliateConversion.objects.filter(external_transaction_id="ORDER_COMBO").count(), 2)

    def test_reconciliation_import_reports_errors_and_rolls_back(self):
        """File CSV có dòng lỗi (thiếu cột, hoa hồng âm, sai ngày) phải bị từ chối và báo lỗi dòng"""
        invalid_csv = (
            "program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code\n"
            "Shopee Vietnam,,ITEM_1,2026-10-25 10:00:00,approved,15000,VND,\n"  # Dòng 2: Thiếu transaction_id
            "Shopee Vietnam,ORD_2,ITEM_1,INVALID_DATE,approved,15000,VND,\n"      # Dòng 3: Sai định dạng ngày
            "Shopee Vietnam,ORD_3,ITEM_1,2026-10-25 10:00:00,unknown_status,15000,VND,\n" # Dòng 4: Sai status
            "Shopee Vietnam,ORD_4,ITEM_1,2026-10-25 10:00:00,approved,-5000,VND,\n" # Dòng 5: Hoa hồng âm
        )
        result = parse_reconciliation_csv(invalid_csv)

        self.assertFalse(result["success"])
        self.assertGreaterEqual(len(result["errors"]), 4)
        # Không có bản ghi nào được ghi vào database do lỗi rollback
        self.assertEqual(AffiliateConversion.objects.count(), 0)

    def test_reconciliation_csv_missing_header_columns(self):
        """File CSV thiếu cột bắt buộc bị từ chối ngay lập tức"""
        bad_header_csv = "program,transaction_id\nShopee Vietnam,SPX_1\n"
        result = parse_reconciliation_csv(bad_header_csv)

        self.assertFalse(result["success"])
        self.assertIn("thiếu các cột bắt buộc", result["errors"][0]["reason"])

    def test_reconciliation_privacy_no_pii_fields(self):
        """Model AffiliateConversion không chứa các trường PII (tên, số điện thoại, địa chỉ)"""
        field_names = [f.name for f in AffiliateConversion._meta.get_fields()]
        self.assertNotIn("customer_name", field_names)
        self.assertNotIn("phone", field_names)
        self.assertNotIn("address", field_names)
        self.assertNotIn("email", field_names)

    def test_separate_currencies_no_arithmetic_mixing(self):
        """Tổng hoa hồng được tách bạch riêng theo từng loại tiền tệ (VND, USD), không cộng dồn lẫn lộn"""
        AffiliateConversion.objects.create(
            program_name="Shopee Vietnam",
            external_transaction_id="TX_VND_1",
            transaction_time=timezone.now(),
            status=ConversionStatusChoices.APPROVED,
            commission_amount=Decimal("150000"),
            currency="VND",
        )
        AffiliateConversion.objects.create(
            program_name="Lazada",
            external_transaction_id="TX_USD_1",
            transaction_time=timezone.now(),
            status=ConversionStatusChoices.APPROVED,
            commission_amount=Decimal("12.50"),
            currency="USD",
        )

        self.client.login(username="admin_staff", password="password123")
        url = reverse("analytics:dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        approved_commissions = response.context["commissions_by_status"][ConversionStatusChoices.APPROVED]
        currencies = [c["currency"] for c in approved_commissions]

        # Cả VND và USD đều xuất hiện trong danh sách riêng rẽ
        self.assertIn("VND", currencies)
        self.assertIn("USD", currencies)
        html_str = response.content.decode("utf-8")
        self.assertTrue("150000" in html_str and "VND" in html_str)
        self.assertTrue("12" in html_str and "USD" in html_str)


    # -------------------------------------------------------------
    # 6. KIỂM THỬ MANAGEMENT COMMAND DỌN DẸP SỰ KIỆN CŨ
    # -------------------------------------------------------------
    def test_cleanup_analytics_events_dry_run(self):
        """Chế độ --dry-run chỉ quét và đếm, không xóa dữ liệu trong database"""
        old_time = timezone.now() - timedelta(days=100)
        pv = PageView.objects.create(product=self.product, path="/old-path/")
        PageView.objects.filter(id=pv.id).update(created_at=old_time)

        click = ClickEvent.objects.create(offer=self.offer, link_mode="direct")
        ClickEvent.objects.filter(id=click.id).update(created_at=old_time)

        out = io.StringIO()
        call_command("cleanup_analytics_events", "--days=90", "--dry-run", stdout=out)

        output_str = out.getvalue()
        self.assertIn("CHẾ ĐỘ DRY-RUN", output_str)
        self.assertIn("Không có dữ liệu nào bị thay đổi", output_str)

        # Dữ liệu vẫn còn nguyên
        self.assertEqual(PageView.objects.filter(id=pv.id).count(), 1)
        self.assertEqual(ClickEvent.objects.filter(id=click.id).count(), 1)

    def test_cleanup_analytics_events_execution(self):
        """Lệnh dọn dẹp xóa sự kiện cũ hơn N ngày nhưng bảo toàn dữ liệu AffiliateConversion"""
        now = timezone.now()
        # Sự kiện mới (30 ngày trước) -> Không bị xóa
        pv_recent = PageView.objects.create(product=self.product, path="/recent/")
        PageView.objects.filter(id=pv_recent.id).update(created_at=now - timedelta(days=30))

        # Sự kiện cũ (120 ngày trước) -> Bị xóa
        pv_old = PageView.objects.create(product=self.product, path="/ancient/")
        PageView.objects.filter(id=pv_old.id).update(created_at=now - timedelta(days=120))

        # Bản ghi đối soát tài chính cũ (120 ngày trước) -> KHÔNG ĐƯỢC XÓA
        conv_old = AffiliateConversion.objects.create(
            program_name="Shopee",
            external_transaction_id="OLD_FINANCIAL_ORDER",
            transaction_time=now - timedelta(days=120),
            status=ConversionStatusChoices.APPROVED,
            commission_amount=Decimal("100000"),
            currency="VND",
        )

        out = io.StringIO()
        call_command("cleanup_analytics_events", "--days=90", stdout=out)

        # Sự kiện cũ bị xóa
        self.assertEqual(PageView.objects.filter(id=pv_old.id).count(), 0)
        # Sự kiện mới còn nguyên
        self.assertEqual(PageView.objects.filter(id=pv_recent.id).count(), 1)
        # Giao dịch đối soát tài chính được bảo toàn nguyên vẹn
        self.assertEqual(AffiliateConversion.objects.filter(id=conv_old.id).count(), 1)
