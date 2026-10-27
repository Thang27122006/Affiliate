from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.catalog.models import Category, Product, StatusChoices
from apps.affiliates.models import Merchant, Offer


class AffiliateConstraintsTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Chuột máy tính",
            slug="chuot-may-tinh",
            status=StatusChoices.PUBLISHED,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Chuột Test",
            brand="TestBrand",
            slug="chuot-test",
            status=StatusChoices.PUBLISHED,
        )
        self.merchant = Merchant.objects.create(
            name="Shopee Vietnam",
            slug="shopee-vn",
            website="https://shopee.vn",
            allowed_hostnames="shopee.vn, s.shopee.vn",
        )

    def test_price_cannot_be_zero_or_negative(self):
        """Không cho phép nhập giá âm hoặc giá bằng 0"""
        offer_zero = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/product-123",
            price=Decimal("0.00"),
        )
        with self.assertRaises(ValidationError) as ctx:
            offer_zero.full_clean()
        self.assertIn("price", ctx.exception.message_dict)

        offer_negative = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/product-123",
            price=Decimal("-150000.00"),
        )
        with self.assertRaises(ValidationError) as ctx:
            offer_negative.full_clean()
        self.assertIn("price", ctx.exception.message_dict)

    def test_price_can_be_null(self):
        """Không có giá thì để trống (None), không dùng 0 để thể hiện 'chưa biết'"""
        offer_no_price = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/product-chua-co-gia",
            price=None,
        )
        offer_no_price.full_clean()
        offer_no_price.save()
        self.assertIsNone(offer_no_price.price)

    def test_valid_positive_decimal_price(self):
        """Giá Decimal dương hợp lệ phải lưu thành công"""
        offer = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://shopee.vn/product-valid",
            price=Decimal("299000.50"),
        )
        offer.full_clean()
        offer.save()
        self.assertEqual(offer.price, Decimal("299000.50"))

    def test_invalid_hostname_rejected(self):
        """URL affiliate không thuộc allowed_hostnames của Merchant phải bị từ chối"""
        offer_unauthorized_host = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://malicious-site.com/fake-deal",
            price=Decimal("100000"),
        )
        with self.assertRaises(ValidationError) as ctx:
            offer_unauthorized_host.full_clean()
        self.assertIn("affiliate_url", ctx.exception.message_dict)

    def test_valid_hostname_accepted(self):
        """URL affiliate thuộc domain hoặc subdomain được phép phải lưu thành công"""
        offer_subdomain = Offer(
            product=self.product,
            merchant=self.merchant,
            affiliate_url="https://s.shopee.vn/deal-hot",
            price=Decimal("150000"),
        )
        offer_subdomain.full_clean()
        offer_subdomain.save()
        self.assertEqual(Offer.objects.count(), 1)
