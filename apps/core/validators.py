import os
from django.core.exceptions import ValidationError
from PIL import Image

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def validate_image_file(file_obj):
    """
    Xác thực an toàn cho tập tin hình ảnh tải lên:
    1. Kiểm tra phần mở rộng: Chỉ chấp nhận JPG, JPEG, PNG, WEBP.
       Chặn hoàn toàn SVG (tránh nguy cơ Stored XSS) và các tệp mã thực thi (.html, .php, .js...).
    2. Kiểm tra dung lượng: Không vượt quá 5MB để bảo vệ bộ nhớ và dung lượng máy chủ.
    3. Kiểm tra tính toàn vẹn và định dạng thực tế bằng Pillow (chống giả mạo đuôi tệp).
    """
    if not file_obj:
        return

    # 1. Kiểm tra phần mở rộng
    ext = os.path.splitext(file_obj.name)[1].lower().lstrip(".")
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Định dạng tệp '.{ext}' không được hỗ trợ. "
            "Chỉ chấp nhận các định dạng hình ảnh chuẩn: JPG, JPEG, PNG, WEBP. "
            "Định dạng SVG hoặc tệp thực thi không được phép tải lên nhằm đảm bảo an toàn hệ thống."
        )

    # 2. Kiểm tra dung lượng tệp
    if hasattr(file_obj, "size") and file_obj.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Dung lượng tệp ({file_obj.size / (1024 * 1024):.1f}MB) vượt quá mức cho phép tối đa là 5.0MB."
        )

    # 3. Kiểm tra header và định dạng thực tế bằng Pillow
    try:
        # Lưu con trỏ đọc hiện tại để restore sau khi inspect
        initial_pos = file_obj.tell() if hasattr(file_obj, "tell") else 0
        img = Image.open(file_obj)
        img.verify()
        real_format = (img.format or "").lower()
        if real_format not in {"jpeg", "png", "webp"}:
            raise ValidationError(
                f"Định dạng hình ảnh thực tế ({real_format.upper()}) không nằm trong danh sách an toàn được phép."
            )
        # Đưa con trỏ file về lại vị trí đầu
        if hasattr(file_obj, "seek"):
            file_obj.seek(initial_pos)
    except Exception as exc:
        if isinstance(exc, ValidationError):
            raise
        raise ValidationError(
            "Tập tin hình ảnh bị lỗi hoặc không thể đọc cấu trúc dữ liệu hình ảnh hợp lệ."
        )
