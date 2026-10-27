import csv
import json
import logging
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db.models import Count, Sum
from apps.affiliates.models import Offer, LinkModeChoices
from .models import ClickEvent, PageView, AffiliateConversion, ConversionStatusChoices
from .reconciliation import parse_reconciliation_csv

logger = logging.getLogger(__name__)
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _sanitize_referrer_path(raw_ref):
    """
    Chuẩn hóa đường dẫn trang nguồn:
    - Chỉ trích xuất đường dẫn nội bộ (bắt đầu bằng /).
    - Cắt bỏ tham số query hoặc hash fragment.
    - Giới hạn tối đa 500 ký tự.
    """
    if not raw_ref or not isinstance(raw_ref, str):
        return ""
    try:
        from urllib.parse import urlsplit
        parsed = urlsplit(raw_ref.strip())
        path = parsed.path
        if path and path.startswith("/"):
            return path[:500]
    except Exception:
        pass
    return ""


@csrf_exempt
@require_POST
def track_click_api_view(request):
    """
    API tiếp nhận sự kiện lượt bấm cho liên kết trực tiếp (Direct Link Tracking).
    """
    data = {}
    try:
        if request.body:
            data = json.loads(request.body.decode("utf-8"))
        elif request.POST:
            data = request.POST.dict()
    except Exception:
        return HttpResponseBadRequest("Dữ liệu gửi lên không đúng định dạng JSON.")

    offer_id = data.get("offer_id")
    if not offer_id:
        return JsonResponse({"status": "error", "message": "Thiếu tham số offer_id."}, status=400)

    try:
        offer_id = int(offer_id)
    except (ValueError, TypeError):
        return JsonResponse({"status": "error", "message": "offer_id phải là số nguyên."}, status=400)

    try:
        offer = Offer.objects.select_related("merchant", "product__category").get(id=offer_id)
    except Offer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Offer không tồn tại."}, status=404)

    if not offer.is_active or not offer.merchant.is_active:
        return JsonResponse({"status": "error", "message": "Offer hoặc Merchant không hoạt động."}, status=400)

    product = offer.product
    category = product.category
    if product.status != "published" or (category and category.status != "published"):
        return JsonResponse({"status": "error", "message": "Sản phẩm chưa được xuất bản."}, status=400)

    # Server-side debounce trong 3 giây theo session
    session_key = request.session.session_key
    if not session_key:
        try:
            request.session.save()
            session_key = request.session.session_key
        except Exception:
            session_key = "anonymous"

    throttle_key = f"throttle_click_{session_key}_{offer_id}"
    if cache.get(throttle_key):
        return JsonResponse({"status": "ignored", "reason": "throttled"})

    cache.set(throttle_key, True, timeout=3)

    raw_ref = data.get("referrer_path") or request.META.get("HTTP_REFERER", "")
    referrer_path = _sanitize_referrer_path(raw_ref)

    try:
        ClickEvent.objects.create(
            offer=offer,
            link_mode=LinkModeChoices.DIRECT,
            referrer_path=referrer_path,
        )
    except Exception as exc:
        logger.error(f"Lỗi khi lưu ClickEvent cho direct click Offer #{offer_id}: {exc}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Lỗi lưu trữ dữ liệu sự kiện."}, status=500)

    return JsonResponse({"status": "ok"})


def _parse_date_range(request):
    """
    Trích xuất và chuẩn hóa khoảng ngày lọc theo múi giờ Asia/Ho_Chi_Minh.
    Mặc định: 30 ngày gần nhất tính đến thời điểm hiện tại.
    """
    now_vn = datetime.now(VIETNAM_TZ)
    today_vn = now_vn.date()
    default_start = today_vn - timedelta(days=30)
    default_end = today_vn

    start_date_str = request.GET.get("start_date", "").strip()
    end_date_str = request.GET.get("end_date", "").strip()

    start_date = default_start
    end_date = default_end

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = default_start

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            end_date = default_end

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Chuyển đổi sang datetime đầu ngày và cuối ngày có timezone aware
    start_dt = datetime.combine(start_date, time.min).replace(tzinfo=VIETNAM_TZ)
    end_dt = datetime.combine(end_date, time.max).replace(tzinfo=VIETNAM_TZ)

    return start_date, end_date, start_dt, end_dt


@staff_member_required(login_url="/admin/login/")
def analytics_dashboard_view(request):
    """
    Báo cáo thống kê nội bộ và đối soát tiếp thị liên kết dành riêng cho Quản trị viên (Staff Only).
    
    NGUYÊN TẮC BÁO CÁO:
    1. Bảo mật: Tách biệt hoàn toàn khỏi trang công khai, yêu cầu quyền staff.
    2. Nhất quán múi giờ: Sử dụng múi giờ chuẩn Asia/Ho_Chi_Minh cho bộ lọc và hiển thị.
    3. Minh bạch số liệu:
       - Số liệu do website đo: Lượt xem trang kỹ thuật (Views) và Lượt bấm đối tác (Clicks).
       - Tỷ lệ CTR sự kiện = (Clicks / Views) * 100; ghi rõ là tỷ lệ sự kiện, không phải unique users.
       - Xử lý chia cho 0 an toàn; không hiển thị số liệu mẫu như số liệu thật.
    4. Đối soát hoa hồng:
       - Phân tách theo trạng thái: Đã duyệt (approved), Chờ duyệt (pending), Bị từ chối (rejected).
       - Tuyệt đối KHÔNG cộng gộp các loại tiền tệ khác nhau (VND, USD...).
       - Chỉ đối chiếu sản phẩm/bài viết khi có tracking code khớp rõ ràng; không tự đoán mò.
    """
    start_date, end_date, start_dt, end_dt = _parse_date_range(request)

    # -------------------------------------------------------------
    # 1. THỐNG KÊ NỘI BỘ (DO WEBSITE ĐO ĐẠC)
    # -------------------------------------------------------------
    product_views_count = PageView.objects.filter(
        product__isnull=False,
        created_at__range=(start_dt, end_dt),
    ).count()

    article_views_count = PageView.objects.filter(
        article__isnull=False,
        created_at__range=(start_dt, end_dt),
    ).count()

    total_page_views = product_views_count + article_views_count

    total_clicks_count = ClickEvent.objects.filter(
        created_at__range=(start_dt, end_dt),
    ).count()

    # Tính CTR sự kiện toàn trang (phòng chống chia cho 0)
    overall_event_ctr = None
    if total_page_views > 0:
        overall_event_ctr = (total_clicks_count / total_page_views) * 100

    # Top sản phẩm có nhiều lượt bấm nhất kèm lượt xem tương ứng
    top_products_query = (
        ClickEvent.objects.filter(created_at__range=(start_dt, end_dt))
        .values("offer__product_id", "offer__product__name", "offer__product__slug")
        .annotate(clicks=Count("id"))
        .order_by("-clicks")[:10]
    )

    top_products = []
    for item in top_products_query:
        pid = item["offer__product_id"]
        # Đếm lượt xem trang của sản phẩm này trong đúng khoảng ngày tương ứng
        p_views = PageView.objects.filter(
            product_id=pid,
            created_at__range=(start_dt, end_dt),
        ).count()
        p_ctr = (item["clicks"] / p_views * 100) if p_views > 0 else None

        top_products.append(
            {
                "product_id": pid,
                "name": item["offer__product__name"],
                "slug": item["offer__product__slug"],
                "clicks": item["clicks"],
                "views": p_views,
                "ctr": p_ctr,
            }
        )

    # Top nơi bán có nhiều lượt bấm nhất
    top_merchants = list(
        ClickEvent.objects.filter(created_at__range=(start_dt, end_dt))
        .values("offer__merchant__name")
        .annotate(clicks=Count("id"))
        .order_by("-clicks")[:10]
    )

    # Top bài viết / trang nguồn phát sinh lượt bấm
    top_referrers = list(
        ClickEvent.objects.filter(created_at__range=(start_dt, end_dt))
        .exclude(referrer_path="")
        .values("referrer_path")
        .annotate(clicks=Count("id"))
        .order_by("-clicks")[:10]
    )

    # -------------------------------------------------------------
    # 2. ĐỐI SOÁT TỪ ĐỐI TÁC (NHẬP TỪ CSV)
    # -------------------------------------------------------------
    conversions_qs = AffiliateConversion.objects.filter(
        transaction_time__range=(start_dt, end_dt),
    )

    # Tổng hợp hoa hồng nhóm theo trạng thái và theo từng loại tiền tệ (KHÔNG cộng gộp tiền tệ)
    commission_grouped_query = (
        conversions_qs.values("status", "currency")
        .annotate(
            total_commission=Sum("commission_amount"),
            count=Count("id"),
        )
        .order_by("status", "currency")
    )

    commissions_by_status = {
        ConversionStatusChoices.APPROVED: [],
        ConversionStatusChoices.PENDING: [],
        ConversionStatusChoices.REJECTED: [],
    }

    for item in commission_grouped_query:
        st = item["status"]
        if st in commissions_by_status:
            commissions_by_status[st].append(
                {
                    "currency": item["currency"],
                    "total": item["total_commission"] or Decimal("0"),
                    "count": item["count"],
                }
            )

    # Thống kê giao dịch đã đối chiếu theo sản phẩm (chỉ khi có tracking_code khớp)
    matched_products_stats = list(
        conversions_qs.filter(matched_product__isnull=False)
        .values("matched_product__name", "currency", "status")
        .annotate(
            total_commission=Sum("commission_amount"),
            order_count=Count("id"),
        )
        .order_by("-total_commission")[:10]
    )

    # 25 giao dịch đối soát gần nhất trong khoảng thời gian lọc
    recent_conversions = (
        conversions_qs.select_related("matched_product", "matched_article")
        .order_by("-transaction_time")[:25]
    )

    context = {
        "title": "Báo Cáo Hiệu Quả & Đối Soát Tiếp Thị Liên Kết | Góc Phụ Kiện",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "timezone_name": "Asia/Ho_Chi_Minh",
        # Số liệu nội bộ
        "product_views_count": product_views_count,
        "article_views_count": article_views_count,
        "total_page_views": total_page_views,
        "total_clicks_count": total_clicks_count,
        "overall_event_ctr": overall_event_ctr,
        "top_products": top_products,
        "top_merchants": top_merchants,
        "top_referrers": top_referrers,
        # Số liệu đối soát
        "commissions_by_status": commissions_by_status,
        "matched_products_stats": matched_products_stats,
        "recent_conversions": recent_conversions,
        "total_conversions_count": conversions_qs.count(),
    }

    return render(request, "analytics/dashboard.html", context)


@staff_member_required(login_url="/admin/login/")
def reconciliation_import_view(request):
    """
    Trang nhập file CSV đối soát hoa hồng từ đối tác tiếp thị liên kết (Staff Only).
    """
    import_result = None

    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            import_result = {
                "success": False,
                "errors": [{"row": 0, "reason": "Vui lòng chọn một tập tin CSV để tải lên."}],
            }
        elif not csv_file.name.lower().endswith(".csv"):
            import_result = {
                "success": False,
                "errors": [{"row": 0, "reason": "Tập tin không đúng định dạng .csv."}],
            }
        else:
            import_result = parse_reconciliation_csv(csv_file)

    context = {
        "title": "Nhập Báo Cáo Đối Soát Hoa Hồng (CSV) | Góc Phụ Kiện",
        "import_result": import_result,
    }
    return render(request, "analytics/import_csv.html", context)


@staff_member_required(login_url="/admin/login/")
def download_sample_csv_view(request):
    """
    Tải về file CSV mẫu định dạng nội bộ để quản trị viên đối chiếu (Staff Only).
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="sample_reconciliation.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "program",
            "transaction_id",
            "item_id",
            "transaction_time",
            "status",
            "commission",
            "currency",
            "tracking_code",
        ]
    )
    writer.writerow(
        [
            "Shopee Vietnam",
            "DEMO_SPX_001",
            "ITEM_01",
            "2026-10-25 14:30:00",
            "approved",
            "15000",
            "VND",
            "prod-chuot-logitech-pebble-m350",
        ]
    )
    writer.writerow(
        [
            "Shopee Vietnam",
            "DEMO_SPX_001",
            "ITEM_02",
            "2026-10-25 14:30:00",
            "approved",
            "22000",
            "VND",
            "prod-ban-phim-keychron-k2",
        ]
    )
    writer.writerow(
        [
            "Tiki",
            "DEMO_TK_089",
            "LINE_A",
            "2026-10-26 09:15:20",
            "pending",
            "35000",
            "VND",
            "art-top-chuot-silent-sinh-vien",
        ]
    )
    writer.writerow(
        [
            "Lazada",
            "DEMO_LAZ_555",
            "ITEM_1",
            "2026-10-27 10:00:00",
            "approved",
            "2.50",
            "USD",
            "prod-chuot-logitech-pebble-m350",
        ]
    )
    return response
