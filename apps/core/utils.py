import re
from decimal import Decimal
from django.utils.text import slugify
import markdown
import bleach


def unique_slugify(instance, value, slug_field_name="slug", max_length=255):
    """
    Tạo slug duy nhất cho một model instance, tránh xung đột.
    Nếu slug đã tồn tại ở bản ghi khác, tự động gắn thêm hậu tố -1, -2,...
    """
    base_slug = slugify(value, allow_unicode=False)
    if not base_slug:
        base_slug = "item"
    
    # Giới hạn chiều dài base slug để chừa chỗ cho hậu tố
    base_slug = base_slug[:max_length - 10].rstrip("-")
    slug = base_slug
    
    model_class = instance.__class__
    counter = 1
    
    # Kiểm tra xem có bị trùng với bản ghi khác không
    while True:
        qs = model_class.objects.filter(**{slug_field_name: slug})
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if not qs.exists():
            break
        counter += 1
        slug = f"{base_slug}-{counter}"
        
    return slug


# Whitelist các thẻ HTML và thuộc tính an toàn cho Bleach khi render Markdown
ALLOWED_TAGS = [
    "p", "div", "span", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "b", "i", "u", "s", "del", "code", "pre",
    "blockquote", "q",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "th", "td",
    "a", "img",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "th": ["scope", "colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
    "*": ["class", "id"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_safe_markdown(text):
    """
    Chuyển đổi text Markdown sang HTML đã được làm sạch (sanitized).
    Chặn tuyệt đối XSS, thẻ script, onclick hoặc iframe không kiểm soát.
    """
    if not text:
        return ""
    
    # Loại bỏ hoàn toàn khối <script>...</script> và <style>...</style> kèm nội dung bên trong
    cleaned_text = re.sub(r"<\s*script[^>]*>[\s\S]*?<\s*/\s*script\s*>", "", text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r"<\s*style[^>]*>[\s\S]*?<\s*/\s*style\s*>", "", cleaned_text, flags=re.IGNORECASE)
    
    # Render Markdown sang HTML cơ bản
    raw_html = markdown.markdown(
        cleaned_text,
        extensions=[
            "extra",
            "codehilite",
            "toc",
            "nl2br",
            "sane_lists",
        ],
        output_format="html5",
    )
    
    # Làm sạch an toàn bằng bleach
    clean_html = bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    
    # Đảm bảo tất cả liên kết ngoài đều có rel="noopener noreferrer"
    clean_html = bleach.linkify(
        clean_html,
        callbacks=[
            lambda attrs, new: (attrs.update({(None, "rel"): "noopener noreferrer"}), attrs)[1]
        ],
    )
    
    return clean_html
