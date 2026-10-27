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


def search_view(request):
    """
    Tìm kiếm toàn trang trên sản phẩm và bài viết đã xuất bản.
    """
    query = request.GET.get("q", "").strip()
    products = []
    articles = []

    if query:
        products = (
            Product.objects.published()
            .filter(
                Q(name__icontains=query)
                | Q(brand__icontains=query)
                | Q(model__icontains=query)
                | Q(short_description__icontains=query)
                | Q(category__name__icontains=query)
            )
            .select_related("category")
            .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
            .distinct()
        )

        articles = (
            Article.objects.published()
            .filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
            )
            .select_related("author")
            .distinct()
        )

    context = {
        "title": f"Tìm kiếm: '{query}' - Góc Phụ Kiện" if query else "Tìm kiếm - Góc Phụ Kiện",
        "query": query,
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
