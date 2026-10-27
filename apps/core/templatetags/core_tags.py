from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Template tag hỗ trợ thay thế hoặc thêm tham số GET query string
    trong khi vẫn bảo toàn nguyên vẹn tất cả các tham số lọc khác.
    Rất hữu ích cho phân trang khi đang có bộ lọc kết hợp (giá, thương hiệu, sắp xếp).
    Cách dùng: <a href="?{% url_replace page=2 %}">Trang 2</a>
    """
    query_dict = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            query_dict.pop(key, None)
        else:
            query_dict[key] = value
    return query_dict.urlencode()


@register.filter
def get_item(dictionary, key):
    """Lấy giá trị theo key từ dictionary trong template"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
