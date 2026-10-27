from django.shortcuts import render
from django.db import connection
from django.db.models import Q, Min
from django.http import JsonResponse
from apps.catalog.models import Category, Product
from apps.content.models import Article


def home_view(request):
    """
    Trang chủ Góc Phụ Kiện:
    Hiển thị thông điệp cốt lõi, danh mục phụ kiện trọng tâm,
    sản phẩm nổi bật và các bài viết đánh giá/cẩm nang mới nhất.
    Chỉ hiển thị dữ liệu đã xuất bản hợp lệ.
    """
    categories = Category.objects.published()
    
    # Sản phẩm đã xuất bản kèm giá tham khảo thấp nhất từ các offer đang hoạt động
    featured_products = (
        Product.objects.published()
        .select_related("category")
        .prefetch_related("images", "offers")
        .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
        .order_by("-created_at")[:6]
    )

    # Bài viết mới nhất đã xuất bản
    latest_articles = (
        Article.objects.published()
        .select_related("author")
        .order_by("-published_at")[:3]
    )

    context = {
        "title": "Góc Phụ Kiện - Đánh giá & So sánh phụ kiện học tập, làm việc sinh viên",
        "categories": categories,
        "featured_products": featured_products,
        "latest_articles": latest_articles,
    }
    return render(request, "core/home.html", context)


def about_view(request):
    """
    Trang giới thiệu sứ mệnh và phương pháp đánh giá minh bạch của Góc Phụ Kiện.
    """
    context = {
        "title": "Về chúng tôi & Phương pháp đánh giá - Góc Phụ Kiện",
    }
    return render(request, "core/about.html", context)


from apps.core.search_utils import clean_search_query, build_search_filter


def search_view(request):
    """
    Tìm kiếm toàn trang trên sản phẩm (tên, thương hiệu, model)
    và bài viết (tiêu đề, tóm tắt) đã xuất bản.
    Xử lý an toàn chuỗi rỗng, khoảng trắng thừa, giới hạn độ dài
    và hỗ trợ tìm kiếm không dấu trên PostgreSQL.
    """
    raw_query = request.GET.get("q", "")
    query = clean_search_query(raw_query, max_length=120)
    products = []
    articles = []

    if query:
        # Lọc sản phẩm theo tên, thương hiệu, model
        product_filter = build_search_filter(["name", "brand", "model"], query)
        products = (
            Product.objects.published()
            .filter(product_filter)
            .select_related("category")
            .prefetch_related("images")
            .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
            .distinct()
            .order_by("-created_at")
        )

        # Lọc bài viết theo tiêu đề, tóm tắt
        article_filter = build_search_filter(["title", "summary"], query)
        articles = (
            Article.objects.published()
            .filter(article_filter)
            .select_related("author")
            .distinct()
            .order_by("-published_at")
        )

    context = {
        "title": f"Tìm kiếm: '{query}' - Góc Phụ Kiện" if query else "Tìm kiếm - Góc Phụ Kiện",
        "query": query,
        "raw_query": raw_query,
        "products": products,
        "articles": articles,
        "total_results": len(products) + len(articles),
    }
    return render(request, "core/search.html", context)


def custom_404_view(request, exception=None):
    """
    Trang thông báo lỗi 404 thân thiện, đồng bộ thiết kế với hệ thống.
    """
    return render(request, "404.html", status=404)


def health_check_view(request):
    """
    Endpoint kiểm tra sức khỏe hệ thống (Health Check) và kết nối PostgreSQL.
    """
    status = "healthy"
    db_status = "connected"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except Exception as exc:
        status = "unhealthy"
        db_status = f"error: {exc}"

    return JsonResponse(
        {
            "status": status,
            "database": db_status,
            "project": "Góc Phụ Kiện",
        },
        status=200 if status == "healthy" else 500,
    )
