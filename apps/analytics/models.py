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
