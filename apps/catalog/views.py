from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Min, Q
from .models import Category, Product


def product_list_view(request):
    """
    Trang tất cả sản phẩm:
    Hiển thị danh sách toàn bộ sản phẩm đã xuất bản, hỗ trợ lọc theo danh mục,
    thương hiệu và tùy chọn sắp xếp.
    """
    products_qs = (
        Product.objects.published()
        .select_related("category")
        .prefetch_related("images", "offers")
        .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
    )

    # Lọc theo danh mục nếu có
    selected_category = request.GET.get("category", "").strip()
    if selected_category:
        products_qs = products_qs.filter(category__slug=selected_category)

    # Lọc theo thương hiệu nếu có
    selected_brand = request.GET.get("brand", "").strip()
    if selected_brand:
        products_qs = products_qs.filter(brand__iexact=selected_brand)

    # Sắp xếp
    sort = request.GET.get("sort", "newest")
    if sort == "name_asc":
        products_qs = products_qs.order_by("name")
    elif sort == "name_desc":
        products_qs = products_qs.order_by("-name")
    elif sort == "price_asc":
        products_qs = products_qs.order_by("min_price")
    else:  # newest
        products_qs = products_qs.order_by("-created_at")

    # Phân trang
    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Tất cả sản phẩm - Góc Phụ Kiện",
        "page_obj": page_obj,
        "selected_category": selected_category,
        "selected_brand": selected_brand,
        "current_sort": sort,
        "total_count": paginator.count,
    }
    return render(request, "catalog/product_list.html", context)


def category_detail_view(request, slug):
    """
    Trang danh mục sản phẩm:
    Hiển thị thông tin danh mục, danh sách sản phẩm đã xuất bản,
    bộ lọc thương hiệu và tùy chọn sắp xếp.
    Chỉ hiển thị Category và Product đã xuất bản.
    """
    category = get_object_or_404(Category.objects.published(), slug=slug)

    # Lấy các thương hiệu hiện có trong danh mục để tạo bộ lọc
    available_brands = (
        Product.objects.published()
        .filter(category=category)
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )

    # Query sản phẩm thuộc danh mục
    products_qs = (
        Product.objects.published()
        .filter(category=category)
        .select_related("category")
        .prefetch_related("images", "offers")
        .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
    )

    # Lọc theo thương hiệu
    selected_brand = request.GET.get("brand", "").strip()
    if selected_brand:
        products_qs = products_qs.filter(brand__iexact=selected_brand)

    # Sắp xếp
    sort = request.GET.get("sort", "newest")
    if sort == "name_asc":
        products_qs = products_qs.order_by("name")
    elif sort == "name_desc":
        products_qs = products_qs.order_by("-name")
    elif sort == "price_asc":
        products_qs = products_qs.order_by("min_price")
    else:  # newest
        products_qs = products_qs.order_by("-created_at")

    # Phân trang
    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": f"{category.name} - Góc Phụ Kiện",
        "category": category,
        "page_obj": page_obj,
        "available_brands": available_brands,
        "selected_brand": selected_brand,
        "current_sort": sort,
        "total_count": paginator.count,
    }
    return render(request, "catalog/category_detail.html", context)


def product_detail_view(request, slug):
    """
    Trang chi tiết sản phẩm:
    Hiển thị thư viện ảnh, thông số kỹ thuật chi tiết, danh sách nơi bán
    (với giá tham khảo & thời điểm kiểm tra giá), và các bài viết liên quan.
    """
    product = get_object_or_404(
        Product.objects.published().select_related("category"),
        slug=slug,
    )

    # Hình ảnh sản phẩm
    images = product.images.all()
    primary_image = images.first() if images.exists() else None

    # Bảng thông số kỹ thuật đã sắp xếp theo thứ tự hiển thị
    specifications = (
        product.specifications
        .select_related("specification_definition")
        .order_by("specification_definition__display_order", "id")
    )

    # Nơi bán đang hoạt động kèm giá tham khảo
    offers = (
        product.offers
        .filter(is_active=True)
        .select_related("merchant")
        .order_by("price")
    )

    # Bài viết liên quan đã xuất bản
    related_articles = (
        product.articles
        .published()
        .select_related("author")
        .order_by("-published_at")[:4]
    )

    # Sản phẩm cùng danh mục gợi ý
    similar_products = (
        Product.objects.published()
        .filter(category=product.category)
        .exclude(pk=product.pk)
        .select_related("category")
        .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))[:3]
    )

    context = {
        "title": f"{product.name} ({product.brand}) - Thông số & Nơi bán | Góc Phụ Kiện",
        "product": product,
        "images": images,
        "primary_image": primary_image,
        "specifications": specifications,
        "offers": offers,
        "related_articles": related_articles,
        "similar_products": similar_products,
    }
    return render(request, "catalog/product_detail.html", context)
