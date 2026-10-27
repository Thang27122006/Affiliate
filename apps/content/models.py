from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
from apps.core.utils import unique_slugify, render_safe_markdown
from apps.catalog.models import PublishedQuerySet, StatusChoices


class ArticleQuerySet(models.QuerySet):
    def published(self):
        """Lọc các bài viết đã xuất bản và thời điểm xuất bản không ở tương lai"""
        return self.filter(
            status=StatusChoices.PUBLISHED,
            published_at__lte=timezone.now(),
        )

    def draft(self):
        """Lọc các bài viết ở trạng thái nháp"""
        return self.filter(status=StatusChoices.DRAFT)


class ArticleTypeChoices(models.TextChoices):
    REVIEW = "review", _("Đánh giá chi tiết")
    BUYING_GUIDE = "buying_guide", _("Cẩm nang chọn mua")
    COMPARISON = "comparison", _("So sánh đối đầu")
    NEWS = "news", _("Tin tức & Xu hướng")


DEFAULT_AFFILIATE_DISCLOSURE = (
    "Công bố minh bạch: Bài viết này có thể chứa liên kết tiếp thị liên kết (affiliate links). "
    "Khi bạn nhấp vào liên kết và mua sản phẩm, chúng tôi có thể nhận được một khoản hoa hồng nhỏ "
    "từ đối tác bán hàng. Khoản phí này hoàn toàn không làm tăng giá bán bạn phải trả và giúp "
    "duy trì nền tảng đánh giá độc lập 'Góc Phụ Kiện'."
)


class Article(TimeStampedModel):
    """
    Bài viết đánh giá, cẩm nang tư vấn hoặc so sánh phụ kiện.
    Tất cả các trường biên tập minh bạch được công khai rõ ràng.
    """
    title = models.CharField(max_length=255, verbose_name="Tiêu đề bài viết")
    slug = models.SlugField(max_length=265, unique=True, verbose_name="Đường dẫn tĩnh (Slug)")
    summary = models.TextField(blank=True, verbose_name="Tóm tắt ngắn gọn")
    content = models.TextField(
        verbose_name="Nội dung bài viết (Markdown)",
        help_text="Nhập nội dung dưới định dạng Markdown an toàn. HTML thô nguy hại sẽ tự động được lọc sạch.",
    )
    article_type = models.CharField(
        max_length=30,
        choices=ArticleTypeChoices.choices,
        default=ArticleTypeChoices.REVIEW,
        verbose_name="Loại bài viết",
    )
    thumbnail = models.ImageField(
        upload_to="articles/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Ảnh đại diện bài viết",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="articles",
        verbose_name="Tác giả",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="Trạng thái",
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Ngày xuất bản",
        help_text="Thời điểm bài viết được công khai chính thức.",
    )
    products = models.ManyToManyField(
        "catalog.Product",
        blank=True,
        related_name="articles",
        verbose_name="Sản phẩm được đề cập",
        help_text="Chọn các sản phẩm được đánh giá hoặc so sánh trong bài viết này.",
    )
    is_demo = models.BooleanField(
        default=False,
        verbose_name="Dữ liệu mẫu (Demo)",
        help_text="Đánh dấu dữ liệu được sinh ra cho mục đích thử nghiệm.",
    )

    # Các trường biên tập minh bạch (Editorial Transparency)
    information_source = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nguồn thông tin tham khảo",
        help_text="Ví dụ: Tài liệu kỹ thuật nhà sản xuất, kết quả đo đạc thực tế.",
    )
    is_hands_on_experience = models.BooleanField(
        default=False,
        verbose_name="Đã trực tiếp trải nghiệm sản phẩm",
        help_text="Tích chọn nếu người viết đã trực tiếp cầm, dùng và kiểm thử sản phẩm thực tế.",
    )
    testing_methodology = models.TextField(
        blank=True,
        verbose_name="Phương pháp thử nghiệm",
        help_text="Mô tả cụ thể cách thử nghiệm (ví dụ: gõ văn bản 8 tiếng/ngày, đo độ nảy switch, kiểm tra kết nối Bluetooth...).",
    )
    testing_duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Thời gian thử nghiệm thực tế",
        help_text="Ví dụ: 3 tuần sử dụng trong môi trường học tập thực tế.",
    )
    affiliate_disclosure = models.TextField(
        default=DEFAULT_AFFILIATE_DISCLOSURE,
        verbose_name="Công bố tiếp thị liên kết",
        help_text="Thông điệp minh bạch bắt buộc hiển thị đến người đọc.",
    )

    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = "Bài viết"
        verbose_name_plural = "Bài viết & Đánh giá"
        ordering = ["-published_at", "-created_at"]
        permissions = [
            ("can_publish_article", "Có thể xuất bản bài viết"),
        ]

    def __str__(self):
        return self.title

    def get_safe_content_html(self):
        """Trả về HTML an toàn đã render từ Markdown và lọc sạch các thẻ nguy hại"""
        return render_safe_markdown(self.content)

    def clean(self):
        super().clean()
        if not self.slug and self.title:
            self.slug = unique_slugify(self, self.title, slug_field_name="slug", max_length=265)
        
        # Nếu chuyển sang xuất bản mà chưa có published_at, tự động gán thời điểm hiện tại
        if self.status == StatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title, slug_field_name="slug", max_length=265)
        if self.status == StatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
