import re
from django.db.models import Q
from django.db import connection


def clean_search_query(raw_query, max_length=120):
    """
    Làm sạch chuỗi tìm kiếm đầu vào:
    - Loại bỏ khoảng trắng đầu/cuối và rút gọn khoảng trắng liên tiếp.
    - Giới hạn độ dài tối đa để tránh lạm dụng bộ nhớ và DoS.
    """
    if not raw_query:
        return ""
    
    cleaned = re.sub(r"\s+", " ", str(raw_query).strip())
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()
    return cleaned


def build_search_filter(fields, query):
    """
    Xây dựng biểu thức Q tìm kiếm đa trường không phân biệt hoa thường.
    Ưu tiên sử dụng lookup __unaccent__icontains của PostgreSQL để hỗ trợ
    tìm kiếm tiếng Việt không dấu (ví dụ: 'chuot' tìm được 'Chuột').
    Fallback an toàn sang __icontains nếu không dùng PostgreSQL hoặc chưa bật extension.
    """
    if not query or not fields:
        return Q()

    # Kiểm tra xem PostgreSQL có đang dùng và extension unaccent có khả dụng không
    is_postgres = connection.vendor == "postgresql"

    q_object = Q()
    for field in fields:
        if is_postgres:
            q_object |= Q(**{f"{field}__unaccent__icontains": query})
        else:
            q_object |= Q(**{f"{field}__icontains": query})

    return q_object
