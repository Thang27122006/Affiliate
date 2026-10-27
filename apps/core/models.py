from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model cung cấp các trường thời gian tạo và cập nhật tự động.
    Được tái sử dụng xuyên suốt toàn bộ dự án.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Thời gian cập nhật")

    class Meta:
        abstract = True
