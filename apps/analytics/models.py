from django.db import models
from apps.affiliates.models import LinkModeChoices


class ClickEvent(models.Model):
    """
    Ghi nhận lượt bấm chuyển hướng tới nơi bán (Affiliate Click).
    
    NGUYÊN TẮC BẢO VỆ QUYỀN RIÊNG TƯ & BẢO MẬT:
    - Tuyệt đối KHÔNG thu thập địa chỉ IP thô.
    - Tuyệt đối KHÔNG thu thập vân tay trình duyệt (fingerprint), cookies định danh
      hoặc thông tin cá nhân (PII) không cần thiết.
    - Dữ liệu này chỉ ghi nhận số lượt bấm kỹ thuật (clicks), KHÔNG phản ánh số người
      dùng duy nhất (unique users) và có thể bị sai lệch bởi bot crawl hoặc các
      tiện ích chặn quảng cáo / tracking của người dùng.
    """
    offer = models.ForeignKey(
        "affiliates.Offer",
        on_delete=models.CASCADE,
        related_name="click_events",
        verbose_name="Offer liên kết",
    )
    link_mode = models.CharField(
        max_length=20,
        choices=LinkModeChoices.choices,
        verbose_name="Hình thức liên kết",
        help_text="Xác định lượt bấm phát sinh từ liên kết trực tiếp (direct) hay chuyển hướng nội bộ (redirect).",
    )
    referrer_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Trang / Bài viết nguồn",
        help_text="Đường dẫn nội bộ trên website nơi người đọc bấm vào liên kết (ví dụ: /san-pham/chuot-logitech-m350/).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Thời điểm bấm",
    )

    class Meta:
        verbose_name = "Lượt bấm nơi bán (Click Event)"
        verbose_name_plural = "Lượt bấm nơi bán (Click Events)"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["offer", "created_at"]),
        ]

    def __str__(self):
        return f"Click #{self.id} -> {self.offer.product.name} ({self.offer.merchant.name}) lúc {self.created_at:%d/%m/%Y %H:%M}"


class PageView(models.Model):
    """
    Ghi nhận lượt xem trang sản phẩm hoặc bài viết nội bộ.
    
    NGUYÊN TẮC GHI NHẬN & BẢO VỆ QUYỀN RIÊNG TƯ:
    - Ghi nhận kỹ thuật lượt tải trang thành công (HTTP 200 GET).
    - Tuyệt đối KHÔNG lưu địa chỉ IP thô, KHÔNG lưu fingerprint, KHÔNG cookie cá nhân.
    - Phản ánh số lượt tải trang (views), KHÔNG phải số người dùng duy nhất (unique visitors).
    - Dữ liệu có thể bị ảnh hưởng bởi bot crawl hoặc trình duyệt tải lại trang.
    """
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="page_views",
        verbose_name="Sản phẩm xem",
    )
    article = models.ForeignKey(
        "content.Article",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="page_views",
        verbose_name="Bài viết xem",
    )
    path = models.CharField(
        max_length=500,
        verbose_name="Đường dẫn trang",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Thời điểm xem",
    )

    class Meta:
        verbose_name = "Lượt xem trang (Page View)"
        verbose_name_plural = "Lượt xem trang (Page Views)"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "created_at"]),
            models.Index(fields=["article", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        target = self.product.name if self.product else (self.article.title if self.article else self.path)
        return f"PageView #{self.id} -> {target} lúc {self.created_at:%d/%m/%Y %H:%M}"


class ConversionStatusChoices(models.TextChoices):
    PENDING = "pending", "Chờ duyệt (Pending)"
    APPROVED = "approved", "Đã duyệt (Approved)"
    REJECTED = "rejected", "Bị từ chối (Rejected)"


class AffiliateConversion(models.Model):
    """
    Dữ liệu giao dịch & hoa hồng được nhập từ báo cáo đối soát của đối tác (Affiliate Reconciliation).
    
    NGUYÊN TẮC QUẢN LÝ DỮ LIỆU ĐỐI SOÁT:
    - Chưa tích hợp API tự động khi chưa có thông tin xác thực chính thức; nhập qua file CSV.
    - Định danh bản ghi duy nhất bởi bộ ba: (program_name, external_transaction_id, external_order_item_id)
      để không gộp nhầm các mặt hàng trong cùng một đơn, đồng thời cho phép import lại để cập nhật
      trạng thái mà không nhân đôi số liệu.
    - Tuyệt đối KHÔNG lưu thông tin cá nhân của người mua (không có tên, số điện thoại, địa chỉ).
    - Chỉ gắn giao dịch với sản phẩm hoặc bài viết khi có tracking code khớp rõ ràng;
      tuyệt đối không phỏng đoán dựa trên thời gian phát sinh gần nhau.
    """
    program_name = models.CharField(
        max_length=120,
        db_index=True,
        verbose_name="Chương trình / Mạng tiếp thị",
        help_text="Ví dụ: Shopee Vietnam, Tiki, Lazada, AccessTrade",
    )
    merchant = models.ForeignKey(
        "affiliates.Merchant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversions",
        verbose_name="Nơi bán hệ thống",
    )
    external_transaction_id = models.CharField(
        max_length=150,
        db_index=True,
        verbose_name="Mã giao dịch đối tác (Order ID)",
    )
    external_order_item_id = models.CharField(
        max_length=150,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Mã dòng mặt hàng (Item ID)",
        help_text="Để trống nếu chương trình đối tác chỉ cung cấp mã đơn tổng hợp.",
    )
    transaction_time = models.DateTimeField(
        verbose_name="Thời gian phát sinh giao dịch",
        db_index=True,
    )
    status = models.CharField(
        max_length=30,
        choices=ConversionStatusChoices.choices,
        default=ConversionStatusChoices.PENDING,
        db_index=True,
        verbose_name="Trạng thái hoa hồng",
    )
    commission_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Số tiền hoa hồng",
    )
    currency = models.CharField(
        max_length=10,
        default="VND",
        db_index=True,
        verbose_name="Đơn vị tiền tệ",
        help_text="Ví dụ: VND, USD (Tuyệt đối không cộng gộp các đơn vị tiền tệ khác nhau).",
    )
    tracking_code = models.CharField(
        max_length=150,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Mã tracking / Sub ID",
        help_text="Mã định danh nguồn do đối tác trả về trong báo cáo đối soát (ví dụ: prod-chuot-m350, art-review-k2).",
    )
    matched_product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversions",
        verbose_name="Sản phẩm đối chiếu được",
    )
    matched_article = models.ForeignKey(
        "content.Article",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversions",
        verbose_name="Bài viết đối chiếu được",
    )
    raw_payload = models.TextField(
        blank=True,
        default="",
        verbose_name="Dữ liệu dòng gốc (JSON/Raw CSV)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời điểm nhập hệ thống",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Thời điểm cập nhật gần nhất",
    )

    class Meta:
        verbose_name = "Giao dịch đối soát (Conversion)"
        verbose_name_plural = "Giao dịch đối soát (Conversions)"
        ordering = ["-transaction_time", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["program_name", "external_transaction_id", "external_order_item_id"],
                name="unique_program_transaction_item",
            )
        ]
        indexes = [
            models.Index(fields=["program_name", "status"]),
            models.Index(fields=["currency", "status"]),
            models.Index(fields=["transaction_time", "status"]),
        ]

    def __str__(self):
        item_suffix = f"/{self.external_order_item_id}" if self.external_order_item_id else ""
        return (
            f"[{self.program_name}] #{self.external_transaction_id}{item_suffix} - "
            f"{self.commission_amount:,.2f} {self.currency} ({self.get_status_display()})"
        )
