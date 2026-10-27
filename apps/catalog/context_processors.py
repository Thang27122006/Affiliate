from .models import Category


def categories_menu(request):
    """
    Context processor cung cấp danh sách danh mục đã xuất bản cho thanh menu điều hướng.
    Sắp xếp theo trường display_order và tên danh mục.
    Tự động ẩn các danh mục đang ở trạng thái Bản nháp (draft).
    """
    return {
        "nav_categories": Category.objects.published().order_by("display_order", "name"),
    }
