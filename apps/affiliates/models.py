from decimal import Decimal
from urllib.parse import urlparse
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.core.utils import unique_slugify


class ActiveQuerySet(models.QuerySet):
    def active(self):
        """Lọc các đối tượng đang hoạt động"""
        return self.filter(is_active=True)


class Merchant(TimeStampedModel):
    """
    Nơi bán / Nhà phân phối phụ kiện (ví dụ: Shopee, Lazada, Tiki, CellphoneS).
    """
    name = models.CharField(max_length=150, unique=True, verbose_name="Tên nơi bán")
    slug = models.SlugField(max_length=160, unique=True, verbose_name="Slug")
    website = models.URLField(verbose_name="Website chính")
    allowed_hostnames = models.TextField(
        verbose_name="Danh sách hostname được chấp nhận",
        help_text=(
            "Nhập các domain/hostname hợp lệ phân tách bằng dấu phẩy hoặc dòng mới. "
            "Ví dụ: shopee.vn, s.shopee.vn, tiki.vn, lazada.vn. "
            "Hệ thống sẽ từ chối các URL affiliate không khớp với hostname được khai báo."
        ),
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    is_demo = models.BooleanField(
        default=False,
        verbose_name="Dữ liệu mẫu (Demo)",
        help_text="Đánh dấu dữ liệu được sinh ra cho mục đích thử nghiệm.",
    )

    objects = ActiveQuerySet.as_manager()

    class Meta:
        verbose_name = "Nơi bán (Merchant)"
        verbose_name_plural = "Nơi bán (Merchants)"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.slug and self.name:
            self.slug = unique_slugify(self, self.name, slug_field_name="slug", max_length=160)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, slug_field_name="slug", max_length=160)
        super().save(*args, **kwargs)

    def get_allowed_hostnames_list(self):
        """Tách và chuẩn hóa danh sách hostname được chấp nhận"""
        if not self.allowed_hostnames:
            return []
        # Chấp nhận phân cách bằng dấu phẩy hoặc xuống dòng
        raw_items = [
            item.strip().lower()
            for line in self.allowed_hostnames.splitlines()
            for item in line.split(",")
            if item.strip()
        ]
        return raw_items

    def is_url_allowed(self, url):
        """Kiểm tra URL có thuộc hostname được chấp thuận hay không"""
        if not url:
            return False
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False
        
        allowed = self.get_allowed_hostnames_list()
        for domain in allowed:
            if hostname == domain or hostname.endswith(f".{domain}"):
                return True
        return False


class Offer(TimeStampedModel):
    """
    Liên kết bán hàng & giá tham khảo của sản phẩm tại một nơi bán (Merchant).
    """
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Sản phẩm",
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.PROTECT,
        related_name="offers",
        verbose_name="Nơi bán",
    )
    affiliate_url = models.URLField(
        max_length=1000,
        verbose_name="URL tiếp thị liên kết (Affiliate URL)",
        help_text="Đường dẫn chuyển tiếp đến nơi bán có gắn tham số tiếp thị liên kết.",
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Giá tham khảo",
        help_text="Giá bán tham khảo. Để trống nếu chưa biết giá; TUYỆT ĐỐI KHÔNG nhập 0.",
    )
    currency = models.CharField(
        max_length=10,
        default="VND",
        verbose_name="Đơn vị tiền tệ",
    )
    price_checked_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Thời điểm kiểm tra giá",
        help_text="Thời điểm gần nhất hệ thống hoặc quản trị viên kiểm tra mức giá này.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Trạng thái hoạt động",
    )
    is_demo = models.BooleanField(
        default=False,
        verbose_name="Dữ liệu mẫu (Demo)",
        help_text="Đánh dấu dữ liệu được sinh ra cho mục đích thử nghiệm.",
    )

    objects = ActiveQuerySet.as_manager()

    class Meta:
        verbose_name = "Nơi bán & Giá tham khảo (Offer)"
        verbose_name_plural = "Nơi bán & Giá tham khảo (Offers)"
        ordering = ["price", "-is_active", "id"]

    def __str__(self):
        price_str = f" - {self.price:,.0f} {self.currency}" if self.price is not None else " - (Chưa có giá)"
        return f"{self.product.name} @ {self.merchant.name}{price_str}"

    def clean(self):
        super().clean()
        # Ràng buộc 1: Không được phép nhập giá <= 0
        if self.price is not None and self.price <= Decimal("0"):
            raise ValidationError(
                {"price": "Giá tham khảo phải lớn hơn 0. Nếu chưa biết giá, vui lòng để trống ô này."}
            )

        # Ràng buộc 2: Hostname của affiliate_url phải thuộc danh sách allowed_hostnames của Merchant
        if self.merchant_id and self.affiliate_url:
            if not self.merchant.is_url_allowed(self.affiliate_url):
                allowed_list = ", ".join(self.merchant.get_allowed_hostnames_list()) or "(chưa khai báo)"
                parsed = urlparse(self.affiliate_url)
                raise ValidationError(
                    {
                        "affiliate_url": (
                            f"Hostname '{parsed.hostname}' không nằm trong danh sách được chấp nhận của "
                            f"nơi bán '{self.merchant.name}'. Các domain được phép: [{allowed_list}]."
                        )
                    }
                )
