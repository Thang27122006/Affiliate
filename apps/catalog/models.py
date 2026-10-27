from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.core.utils import unique_slugify


class PublishedQuerySet(models.QuerySet):
    def published(self):
        """Lọc các bản ghi ở trạng thái đã xuất bản và không phải demo nếu cần"""
        return self.filter(status=StatusChoices.PUBLISHED)

    def draft(self):
        """Lọc các bản ghi ở trạng thái nháp"""
        return self.filter(status=StatusChoices.DRAFT)


class StatusChoices(models.TextChoices):
    DRAFT = "draft", _("Bản nháp")
    PUBLISHED = "published", _("Đã xuất bản")


class DataTypeChoices(models.TextChoices):
    TEXT = "text", _("Văn bản ngắn")
    NUMBER = "number", _("Số")
    BOOLEAN = "boolean", _("Đúng / Sai (Có/Không)")
    SELECT = "select", _("Lựa chọn cố định")


class Category(TimeStampedModel):
    """
    Danh mục sản phẩm (ví dụ: Chuột máy tính, Bàn phím, Giá đỡ laptop).
    """
    name = models.CharField(max_length=150, verbose_name="Tên danh mục")
    slug = models.SlugField(max_length=160, unique=True, verbose_name="Đường dẫn tĩnh (Slug)")
    description = models.TextField(blank=True, verbose_name="Mô tả danh mục")
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="Trạng thái",
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị",
        help_text="Số nhỏ hơn sẽ hiển thị trước trên thanh menu và danh sách.",
    )
    is_demo = models.BooleanField(
        default=False,
        verbose_name="Dữ liệu mẫu (Demo)",
        help_text="Đánh dấu dữ liệu được sinh ra cho mục đích thử nghiệm.",
    )

    objects = PublishedQuerySet.as_manager()

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục sản phẩm"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("catalog:category_detail", kwargs={"slug": self.slug})

    def clean(self):
        super().clean()
        if not self.slug and self.name:
            self.slug = unique_slugify(self, self.name, slug_field_name="slug", max_length=160)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, slug_field_name="slug", max_length=160)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    """
    Sản phẩm phụ kiện được đánh giá, so sánh.
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Danh mục",
    )
    name = models.CharField(max_length=255, verbose_name="Tên sản phẩm")
    slug = models.SlugField(max_length=265, unique=True, verbose_name="Đường dẫn tĩnh (Slug)")
    brand = models.CharField(max_length=100, verbose_name="Thương hiệu")
    model = models.CharField(max_length=100, blank=True, verbose_name="Mã model")
    short_description = models.TextField(blank=True, verbose_name="Mô tả ngắn")
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="Trạng thái xuất bản",
    )
    is_demo = models.BooleanField(
        default=False,
        verbose_name="Dữ liệu mẫu (Demo)",
        help_text="Đánh dấu dữ liệu được sinh ra cho mục đích thử nghiệm.",
    )

    objects = PublishedQuerySet.as_manager()

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ["-created_at"]
        permissions = [
            ("can_publish_product", "Có thể xuất bản sản phẩm"),
        ]

    def __str__(self):
        return f"{self.brand} {self.name}".strip()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    def clean(self):
        super().clean()
        if not self.slug and self.name:
            slug_base = f"{self.brand} {self.name}".strip() if self.brand else self.name
            self.slug = unique_slugify(self, slug_base, slug_field_name="slug", max_length=265)

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_base = f"{self.brand} {self.name}".strip() if self.brand else self.name
            self.slug = unique_slugify(self, slug_base, slug_field_name="slug", max_length=265)
        super().save(*args, **kwargs)


class ProductImage(TimeStampedModel):
    """
    Hình ảnh của sản phẩm.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Sản phẩm",
    )
    image = models.ImageField(upload_to="products/%Y/%m/", verbose_name="Hình ảnh")
    alt_text = models.CharField(
        max_length=255,
        verbose_name="Văn bản thay thế (Alt text)",
        help_text="Mô tả hình ảnh phục vụ trợ năng và tối ưu SEO.",
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")

    class Meta:
        verbose_name = "Hình ảnh sản phẩm"
        verbose_name_plural = "Hình ảnh sản phẩm"
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"Ảnh cho {self.product.name} ({self.alt_text[:30]})"

    def clean(self):
        super().clean()
        if self.image:
            from apps.core.validators import validate_image_file
            if hasattr(self.image, "file"):
                validate_image_file(self.image.file)


class SpecificationDefinition(TimeStampedModel):
    """
    Định nghĩa một thông số kỹ thuật thuộc một danh mục cụ thể.
    Ví dụ trong danh mục 'Chuột máy tính': DPI tối đa, Loại kết nối, Kiểu cầm (Grip).
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="spec_definitions",
        verbose_name="Danh mục áp dụng",
    )
    name = models.CharField(max_length=150, verbose_name="Tên thông số")
    key = models.CharField(
        max_length=60,
        verbose_name="Mã khóa (Key)",
        help_text="Mã định danh duy nhất trong danh mục, viết thường không dấu (ví dụ: dpi, connection_type).",
    )
    unit = models.CharField(max_length=30, blank=True, verbose_name="Đơn vị đo (nếu có)")
    data_type = models.CharField(
        max_length=20,
        choices=DataTypeChoices.choices,
        default=DataTypeChoices.TEXT,
        verbose_name="Kiểu dữ liệu",
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")

    class Meta:
        verbose_name = "Định nghĩa thông số"
        verbose_name_plural = "Định nghĩa thông số"
        ordering = ["category", "display_order", "name"]
        unique_together = [("category", "key")]

    def __str__(self):
        unit_str = f" ({self.unit})" if self.unit else ""
        return f"[{self.category.name}] {self.name}{unit_str}"


class ProductSpecification(TimeStampedModel):
    """
    Giá trị thông số kỹ thuật thực tế của một sản phẩm.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specifications",
        verbose_name="Sản phẩm",
    )
    specification_definition = models.ForeignKey(
        SpecificationDefinition,
        on_delete=models.PROTECT,
        related_name="product_values",
        verbose_name="Định nghĩa thông số",
    )
    value = models.CharField(max_length=255, verbose_name="Giá trị thông số")

    class Meta:
        verbose_name = "Thông số sản phẩm"
        verbose_name_plural = "Thông số sản phẩm"
        unique_together = [("product", "specification_definition")]
        ordering = ["specification_definition__display_order", "id"]

    def __str__(self):
        return f"{self.product.name} - {self.specification_definition.name}: {self.value}"

    def clean(self):
        super().clean()
        # Ràng buộc nghiêm ngặt: Định nghĩa thông số phải thuộc cùng danh mục với sản phẩm
        if self.product_id and self.specification_definition_id:
            product_cat = self.product.category
            spec_cat = self.specification_definition.category
            if product_cat != spec_cat:
                raise ValidationError(
                    {
                        "specification_definition": (
                            f"Thông số '{self.specification_definition.name}' thuộc danh mục '{spec_cat.name}', "
                            f"không khớp với danh mục '{product_cat.name}' của sản phẩm '{self.product.name}'."
                        )
                    }
                )
