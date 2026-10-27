from decimal import Decimal
from urllib.parse import urlsplit, urlencode
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.core.utils import unique_slugify


class ActiveQuerySet(models.QuerySet):
    def active(self):
        """Lọc các đối tượng đang hoạt động"""
        return self.filter(is_active=True)


class LinkModeChoices(models.TextChoices):
    DIRECT = "direct", "Liên kết trực tiếp (Direct Link)"
    REDIRECT = "redirect", "Chuyển hướng nội bộ (Internal Redirect)"


class OfferLinkModeChoices(models.TextChoices):
    USE_MERCHANT = "use_merchant", "Theo cấu hình nơi bán (Mặc định)"
    DIRECT = "direct", "Bắt buộc liên kết trực tiếp"
    REDIRECT = "redirect", "Bắt buộc chuyển hướng nội bộ"


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
    link_mode = models.CharField(
        max_length=20,
        choices=LinkModeChoices.choices,
        default=LinkModeChoices.DIRECT,
        verbose_name="Chế độ liên kết mặc định",
        help_text=(
            "Mặc định là 'Liên kết trực tiếp' để tuân thủ điều khoản các sàn chưa cho phép redirect/cloaking. "
            "Chỉ bật 'Chuyển hướng nội bộ' khi đã xác minh điều khoản chiến dịch cho phép."
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
        raw_items = [
            item.strip().lower()
            for line in self.allowed_hostnames.splitlines()
            for item in line.split(",")
            if item.strip()
        ]
        return raw_items

    def is_url_allowed(self, url):
        """
        Kiểm tra an toàn liên kết theo các tiêu chuẩn khắt khe:
        1. Bắt buộc scheme HTTPS (chặn http, javascript:, data:, file:, v.v.).
        2. Chặn URL có thông tin đăng nhập (credentials username/password).
        3. Hostname phải khớp chính xác hoặc là subdomain chuẩn của allowed_hostnames.
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlsplit(url.strip())
        except Exception:
            return False

        # 1. Bắt buộc HTTPS
        if (parsed.scheme or "").lower() != "https":
            return False

        # 2. Chặn thông tin đăng nhập trong URL (ví dụ: https://user:pass@domain)
        if parsed.username is not None or parsed.password is not None:
            return False
        if "@" in (parsed.netloc or ""):
            return False

        # 3. Kiểm tra hostname hợp lệ
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False

        # So khớp an toàn với allowed_hostnames của Merchant
        allowed = self.get_allowed_hostnames_list()
        for domain in allowed:
            domain = domain.lower().strip()
            if not domain:
                continue
            # Khớp chính xác (domain.com) hoặc là subdomain hợp lệ (*.domain.com)
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
        help_text="Đường dẫn chuyển tiếp đến nơi bán có gắn tham số tiếp thị liên kết từ quản trị viên.",
    )
    link_mode = models.CharField(
        max_length=20,
        choices=OfferLinkModeChoices.choices,
        default=OfferLinkModeChoices.USE_MERCHANT,
        verbose_name="Chế độ liên kết cho Offer này",
        help_text=(
            "Mặc định theo cấu hình nơi bán. Có thể ghi đè riêng cho Offer này "
            "nếu chiến dịch cụ thể yêu cầu direct link hoặc cho phép redirect."
        ),
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

    def get_effective_link_mode(self):
        """Xác định chế độ liên kết thực tế có hiệu lực của Offer"""
        if self.link_mode == OfferLinkModeChoices.DIRECT:
            return LinkModeChoices.DIRECT
        if self.link_mode == OfferLinkModeChoices.REDIRECT:
            return LinkModeChoices.REDIRECT
        if self.merchant_id and self.merchant:
            return self.merchant.link_mode
        return LinkModeChoices.DIRECT

    def get_destination_url(self, referrer_path=None):
        """
        Trả về URL điều hướng phù hợp với chế độ liên kết:
        - Nếu 'direct': trả về trực tiếp affiliate_url (giữ nguyên mọi tham số tracking).
        - Nếu 'redirect': trả về đường dẫn nội bộ /go/<offer_id>/.
        """
        if self.get_effective_link_mode() == LinkModeChoices.REDIRECT:
            url = reverse("affiliates:redirect_to_offer", kwargs={"offer_id": self.id})
            if referrer_path:
                url = f"{url}?{urlencode({'ref': referrer_path})}"
            return url
        return self.affiliate_url

    def clean(self):
        super().clean()
        # Ràng buộc 1: Không được phép nhập giá <= 0
        if self.price is not None and self.price <= Decimal("0"):
            raise ValidationError(
                {"price": "Giá tham khảo phải lớn hơn 0. Nếu chưa biết giá, vui lòng để trống ô này."}
            )

        # Ràng buộc 2: Kiểm tra an toàn khắt khe cho affiliate_url
        if self.affiliate_url:
            raw_url = self.affiliate_url.strip()
            try:
                parsed = urlsplit(raw_url)
            except Exception:
                raise ValidationError({"affiliate_url": "Định dạng URL không hợp lệ."})

            # Chặn giao thức không an toàn (bắt buộc HTTPS)
            scheme = (parsed.scheme or "").lower()
            if scheme != "https":
                raise ValidationError(
                    {
                        "affiliate_url": (
                            f"Giao thức '{scheme}:' không được chấp nhận. "
                            "Hệ thống bắt buộc phải sử dụng giao thức HTTPS bảo mật."
                        )
                    }
                )

            # Chặn thông tin đăng nhập trong URL
            if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
                raise ValidationError(
                    {"affiliate_url": "URL không được phép chứa thông tin xác thực (username/password)."}
                )

            # Hostname phải thuộc danh sách allowed_hostnames của Merchant
            if self.merchant_id:
                if not self.merchant.is_url_allowed(raw_url):
                    allowed_list = ", ".join(self.merchant.get_allowed_hostnames_list()) or "(chưa khai báo)"
                    hostname = (parsed.hostname or "").lower()
                    raise ValidationError(
                        {
                            "affiliate_url": (
                                f"Hostname '{hostname}' không nằm trong danh sách được chấp nhận của "
                                f"nơi bán '{self.merchant.name}'. Các domain được phép: [{allowed_list}]."
                            )
                        }
                    )

