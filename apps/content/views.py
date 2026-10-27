from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Min
from .models import Article, ArticleTypeChoices


def article_list_view(request):
    """
    Trang danh sách bài viết:
    Hỗ trợ lọc theo loại bài (Đánh giá, Cẩm nang chọn mua, So sánh, Tin tức),
    tìm kiếm theo từ khóa và phân trang.
    Chỉ hiển thị các bài viết đã xuất bản và không có lịch tương lai.
    """
    articles_qs = Article.objects.published().select_related("author")

    # Lọc theo loại bài viết
    selected_type = request.GET.get("type", "").strip()
    if selected_type and selected_type in ArticleTypeChoices.values:
        articles_qs = articles_qs.filter(article_type=selected_type)

    # Tìm kiếm nhanh trong bài viết
    search_query = request.GET.get("q", "").strip()
    if search_query:
        articles_qs = articles_qs.filter(
            Q(title__icontains=search_query)
            | Q(summary__icontains=search_query)
            | Q(content__icontains=search_query)
        )

    # Sắp xếp bài mới nhất lên đầu
    articles_qs = articles_qs.order_by("-published_at")

    # Phân trang (9 bài viết / trang)
    paginator = Paginator(articles_qs, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Bài viết & Đánh giá phụ kiện - Góc Phụ Kiện",
        "page_obj": page_obj,
        "selected_type": selected_type,
        "type_choices": ArticleTypeChoices.choices,
        "search_query": search_query,
        "total_count": paginator.count,
    }
    return render(request, "content/article_list.html", context)


def article_detail_view(request, slug):
    """
    Trang chi tiết bài viết:
    Hiển thị thông tin tác giả, ngày cập nhật, các trường biên tập minh bạch
    (trạng thái test thực tế, phương pháp thử, nguồn tin, công bố affiliate),
    nội dung Markdown được làm sạch an toàn, và danh sách sản phẩm được đề cập.
    """
    article = get_object_or_404(
        Article.objects.published().select_related("author"),
        slug=slug,
    )

    # Render HTML an toàn từ Markdown đã làm sạch
    safe_content_html = article.get_safe_content_html()

    # Danh sách sản phẩm được đề cập trong bài viết (chỉ lấy sản phẩm đã xuất bản)
    mentioned_products = (
        article.products
        .published()
        .select_related("category")
        .prefetch_related("images")
        .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
    )

    # Bài viết liên quan cùng thể loại
    related_articles = (
        Article.objects.published()
        .filter(article_type=article.article_type)
        .exclude(pk=article.pk)
        .select_related("author")
        .order_by("-published_at")[:3]
    )

    # Ghi nhận lượt xem bài viết an toàn
    if request.method == "GET":
        try:
            from apps.analytics.models import PageView
            PageView.objects.create(
                article=article,
                path=request.path[:500],
            )
        except Exception:
            pass

    context = {
        "title": f"{article.title} - Góc Phụ Kiện",
        "article": article,
        "safe_content_html": safe_content_html,
        "mentioned_products": mentioned_products,
        "related_articles": related_articles,
    }
    return render(request, "content/article_detail.html", context)

