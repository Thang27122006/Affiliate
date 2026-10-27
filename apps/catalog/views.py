from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import F, Min, Q
from .models import Category, Product, SpecificationDefinition, StatusChoices


def apply_product_filters(products_qs, request, base_category=None):
    """
    Áp dụng bộ lọc danh mục, thương hiệu, khoảng giá tham khảo và tùy chọn sắp xếp
    trên queryset Product đã annotate min_price.
    - min_price là giá thấp nhất ghi nhận từ các Offer đang hoạt động.
    - Sản phẩm chưa có giá (min_price is null) được xử lý riêng, không coi là 0 đồng.
    - Trả về dictionary chứa queryset đã lọc cùng trạng thái các bộ lọc.
    """
    selected_category = ""
    if not base_category:
        selected_category = request.GET.get("category", "").strip()
        if selected_category:
            products_qs = products_qs.filter(category__slug=selected_category)

    selected_brand = request.GET.get("brand", "").strip()
    if selected_brand:
        products_qs = products_qs.filter(brand__iexact=selected_brand)

    price_range = request.GET.get("price_range", "").strip()
    price_min_raw = request.GET.get("price_min", "").strip()
    price_max_raw = request.GET.get("price_max", "").strip()
    no_price = request.GET.get("no_price", "").strip() in ("1", "true", "True")

    price_min = None
    price_max = None

    if price_range == "under_300":
        price_max = Decimal("300000")
    elif price_range == "300_700":
        price_min = Decimal("300000")
        price_max = Decimal("700000")
    elif price_range == "700_1500":
        price_min = Decimal("700000")
        price_max = Decimal("1500000")
    elif price_range == "above_1500":
        price_min = Decimal("1500000")
    elif price_range == "no_price":
        no_price = True

    # Nhập giá tùy chỉnh
    if price_min_raw:
        try:
            val = Decimal(price_min_raw.replace(".", "").replace(",", ""))
            if val >= 0:
                price_min = val
        except (ValueError, InvalidOperation):
            pass

    if price_max_raw:
        try:
            val = Decimal(price_max_raw.replace(".", "").replace(",", ""))
            if val >= 0:
                price_max = val
        except (ValueError, InvalidOperation):
            pass

    # Áp dụng logic lọc giá
    if no_price:
        # Chỉ lọc sản phẩm chưa có giá tham khảo
        products_qs = products_qs.filter(min_price__isnull=True)
    elif price_min is not None or price_max is not None:
        price_filter = Q()
        if price_min is not None:
            price_filter &= Q(min_price__gte=price_min)
        if price_max is not None:
            price_filter &= Q(min_price__lte=price_max)
        products_qs = products_qs.filter(price_filter)

    # Sắp xếp
    sort = request.GET.get("sort", "newest").strip()
    if sort == "name_asc":
        products_qs = products_qs.order_by("name")
    elif sort == "name_desc":
        products_qs = products_qs.order_by("-name")
    elif sort == "price_asc":
        # nulls_last=True đảm bảo sản phẩm chưa có giá luôn đứng cuối, không bị đưa lên đầu coi là 0đ
        products_qs = products_qs.order_by(F("min_price").asc(nulls_last=True), "-created_at")
    elif sort == "price_desc":
        # nulls_last=True cũng đảm bảo sản phẩm chưa có giá đứng cuối
        products_qs = products_qs.order_by(F("min_price").desc(nulls_last=True), "-created_at")
    else:  # newest
        products_qs = products_qs.order_by("-created_at")

    has_active_filters = bool(
        selected_category
        or selected_brand
        or price_range
        or price_min_raw
        or price_max_raw
        or no_price
    )

    return {
        "products_qs": products_qs,
        "selected_category": selected_category,
        "selected_brand": selected_brand,
        "price_min": price_min_raw,
        "price_max": price_max_raw,
        "price_range": price_range,
        "no_price": no_price,
        "current_sort": sort,
        "has_active_filters": has_active_filters,
    }


def product_list_view(request):
    """
    Trang tất cả sản phẩm:
    Hiển thị danh sách toàn bộ sản phẩm đã xuất bản, hỗ trợ lọc theo danh mục,
    thương hiệu, khoảng giá tham khảo và tùy chọn sắp xếp.
    """
    base_qs = (
        Product.objects.published()
        .filter(category__status=StatusChoices.PUBLISHED)
        .select_related("category")
        .prefetch_related("images", "offers")
        .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
    )

    filter_result = apply_product_filters(base_qs, request)
    products_qs = filter_result["products_qs"]

    # Thương hiệu sẵn có để hiển thị trong bộ lọc
    if filter_result["selected_category"]:
        available_brands = (
            Product.objects.published()
            .filter(category__slug=filter_result["selected_category"])
            .values_list("brand", flat=True)
            .distinct()
            .order_by("brand")
        )
    else:
        available_brands = (
            Product.objects.published()
            .filter(category__status=StatusChoices.PUBLISHED)
            .values_list("brand", flat=True)
            .distinct()
            .order_by("brand")
        )

    # Phân trang phía máy chủ (Server-side pagination)
    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Tất cả sản phẩm - Góc Phụ Kiện",
        "page_obj": page_obj,
        "selected_category": filter_result["selected_category"],
        "selected_brand": filter_result["selected_brand"],
        "price_min": filter_result["price_min"],
        "price_max": filter_result["price_max"],
        "price_range": filter_result["price_range"],
        "no_price": filter_result["no_price"],
        "current_sort": filter_result["current_sort"],
        "has_active_filters": filter_result["has_active_filters"],
        "available_brands": available_brands,
        "total_count": paginator.count,
    }
    return render(request, "catalog/product_list.html", context)


def category_detail_view(request, slug):
    """
    Trang danh mục sản phẩm:
    Hiển thị thông tin danh mục, danh sách sản phẩm đã xuất bản thuộc danh mục,
    bộ lọc thương hiệu, khoảng giá tham khảo và tùy chọn sắp xếp.
    Chỉ hiển thị Category và Product đã xuất bản.
    """
    category = get_object_or_404(Category.objects.published(), slug=slug)

    # Thương hiệu hiện có trong danh mục
    available_brands = (
        Product.objects.published()
        .filter(category=category)
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )

    base_qs = (
        Product.objects.published()
        .filter(category=category)
        .select_related("category")
        .prefetch_related("images", "offers")
        .annotate(min_price=Min("offers__price", filter=Q(offers__is_active=True)))
    )

    filter_result = apply_product_filters(base_qs, request, base_category=category)
    products_qs = filter_result["products_qs"]

    # Phân trang phía máy chủ
    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": f"{category.name} - Góc Phụ Kiện",
        "category": category,
        "page_obj": page_obj,
        "available_brands": available_brands,
        "selected_brand": filter_result["selected_brand"],
        "price_min": filter_result["price_min"],
        "price_max": filter_result["price_max"],
        "price_range": filter_result["price_range"],
        "no_price": filter_result["no_price"],
        "current_sort": filter_result["current_sort"],
        "has_active_filters": filter_result["has_active_filters"],
        "total_count": paginator.count,
    }
    return render(request, "catalog/category_detail.html", context)


def product_compare_view(request):
    """
    Trang so sánh đối đầu sản phẩm:
    - Cho phép so sánh từ 2 đến tối đa 3 sản phẩm cùng danh mục.
    - Không thêm trùng sản phẩm.
    - Bảng so sánh gồm ảnh, tên, thông số kỹ thuật, giá tham khảo,
      thời điểm kiểm tra giá và nơi bán đối tác.
    - Thuộc tính thiếu hiển thị "Chưa có thông tin".
    - Thứ tự thông số lấy từ định nghĩa chung của danh mục (display_order).
    - Không tự suy ra sản phẩm tốt nhất.
    """
    raw_p = request.GET.getlist("p")
    slugs = []
    for item in raw_p:
        for s in str(item).split(","):
            cleaned = s.strip()
            if cleaned and cleaned not in slugs:
                slugs.append(cleaned)

    categories = Category.objects.published().order_by("display_order", "name")
    error_message = None
    category = None
    products = []
    spec_rows = []
    other_category_products = []

    if len(slugs) > 3:
        error_message = "Hệ thống chỉ hỗ trợ so sánh tối đa 3 sản phẩm cùng lúc. Vui lòng bỏ bớt sản phẩm."
    elif len(slugs) == 0:
        # Chưa chọn sản phẩm nào: hiển thị giao diện hướng dẫn chọn sản phẩm
        pass
    else:
        # Truy vấn sản phẩm đã xuất bản (kèm category đã xuất bản)
        products_qs = (
            Product.objects.published()
            .filter(slug__in=slugs, category__status=StatusChoices.PUBLISHED)
            .select_related("category")
            .prefetch_related(
                "images",
                "offers__merchant",
                "specifications__specification_definition",
            )
        )
        products_map = {p.slug: p for p in products_qs}
        # Bảo toàn thứ tự slug người dùng gửi lên
        products = [products_map[s] for s in slugs if s in products_map]

        if len(products) < 2:
            error_message = "Vui lòng chọn tối thiểu 2 sản phẩm hợp lệ đã xuất bản để thực hiện so sánh."
            if len(products) == 1:
                category = products[0].category
        else:
            # Kiểm tra cùng danh mục
            distinct_category_ids = {p.category_id for p in products}
            if len(distinct_category_ids) > 1:
                error_message = "Chỉ có thể so sánh các sản phẩm trong cùng một danh mục (ví dụ: cùng là Chuột hoặc cùng là Bàn phím)."
            else:
                category = products[0].category

                # Lấy danh sách định nghĩa thông số của danh mục chung theo thứ tự
                spec_definitions = (
                    SpecificationDefinition.objects
                    .filter(category=category)
                    .order_by("display_order", "id")
                )

                # Dựng dữ liệu giá tham khảo và nơi bán cho từng sản phẩm
                for prod in products:
                    prod.primary_img = prod.images.first()
                    active_offers = [o for o in prod.offers.all() if o.is_active]
                    priced_offers = sorted([o for o in active_offers if o.price is not None], key=lambda x: x.price)
                    prod.best_offer = priced_offers[0] if priced_offers else None
                    prod.min_price = prod.best_offer.price if prod.best_offer else None
                    prod.last_checked = prod.best_offer.price_checked_at if prod.best_offer else None
                    prod.active_offers_list = active_offers

                    # Map specs theo specification_definition_id
                    prod.spec_map = {
                        spec.specification_definition_id: spec.value
                        for spec in prod.specifications.all()
                    }

                # Xây dựng ma trận thông số
                for sdef in spec_definitions:
                    row_values = []
                    for prod in products:
                        val = prod.spec_map.get(sdef.id)
                        if val is not None and str(val).strip() != "":
                            display_val = f"{val} {sdef.unit}".strip() if sdef.unit else str(val)
                            has_val = True
                        else:
                            display_val = "Chưa có thông tin"
                            has_val = False

                        row_values.append({
                            "display": display_val,
                            "has_value": has_val,
                        })

                    spec_rows.append({
                        "name": sdef.name,
                        "unit": sdef.unit,
                        "values": row_values,
                    })

                # Gợi ý thêm sản phẩm cùng danh mục nếu chưa đủ 3 sản phẩm
                if len(products) < 3:
                    other_category_products = (
                        Product.objects.published()
                        .filter(category=category)
                        .exclude(id__in=[p.id for p in products])
                        .order_by("name")
                    )

                # Sinh remove_url an toàn cho từng sản phẩm
                for prod in products:
                    other_slugs = [p.slug for p in products if p.slug != prod.slug]
                    if other_slugs:
                        query_part = "&".join(f"p={s}" for s in other_slugs)
                        prod.remove_url = f"?{query_part}"
                    else:
                        prod.remove_url = "?"

    can_add_more = bool(other_category_products and len(products) < 3)
    has_valid_comparison = bool(len(products) >= 2 and not error_message)

    context = {
        "title": f"So sánh {category.name if category else 'sản phẩm'} - Góc Phụ Kiện",
        "category": category,
        "products": products,
        "spec_rows": spec_rows,
        "error_message": error_message,
        "categories": categories,
        "other_category_products": other_category_products,
        "can_add_more": can_add_more,
        "has_valid_comparison": has_valid_comparison,
        "selected_slugs": slugs,
    }
    return render(request, "catalog/compare.html", context)


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

    # Ghi nhận lượt xem trang an toàn (không làm gián đoạn người đọc nếu có sự cố)
    if request.method == "GET":
        try:
            from apps.analytics.models import PageView
            PageView.objects.create(
                product=product,
                path=request.path[:500],
            )
        except Exception:
            pass

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

