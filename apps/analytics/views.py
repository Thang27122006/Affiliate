import json
import logging
from urllib.parse import urlsplit
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from apps.affiliates.models import Offer, LinkModeChoices
from .models import ClickEvent

logger = logging.getLogger(__name__)


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
    
    Đặc điểm kỹ thuật:
    - Hỗ trợ cả navigator.sendBeacon và fetch(..., { keepalive: true }).
    - Tuyệt đối không thu thập IP thô, fingerprint, cookies theo dõi định danh.
    - Hạn chế gửi sự kiện lặp tức thời (Debounce / Throttle 3 giây theo session).
    - Chỉ ghi nhận với Offer hợp lệ, đang hoạt động và thuộc sản phẩm đã xuất bản.
    """
    # 1. Trích xuất dữ liệu JSON hoặc POST body
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

    # 2. Truy vấn Offer và kiểm tra tính hợp lệ
    try:
        offer = Offer.objects.select_related("merchant", "product__category").get(id=offer_id)
    except Offer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Offer không tồn tại."}, status=404)

    # Kiểm tra trạng thái hoạt động và xuất bản
    if not offer.is_active or not offer.merchant.is_active:
        return JsonResponse({"status": "error", "message": "Offer hoặc Merchant không hoạt động."}, status=400)

    product = offer.product
    category = product.category
    if product.status != "published" or (category and category.status != "published"):
        return JsonResponse({"status": "error", "message": "Sản phẩm chưa được xuất bản."}, status=400)

    # 3. Chống gửi sự kiện lặp tức thời (Server-side debounce trong vòng 3 giây)
    session_key = request.session.session_key
    if not session_key:
        try:
            request.session.save()
            session_key = request.session.session_key
        except Exception:
            session_key = "anonymous"

    throttle_key = f"throttle_click_{session_key}_{offer_id}"
    if cache.get(throttle_key):
        # Đã ghi nhận click cho offer này từ cùng session trong 3 giây qua -> bỏ qua để chống spam
        return JsonResponse({"status": "ignored", "reason": "throttled"})

    # Thiết lập timeout chống spam 3 giây
    cache.set(throttle_key, True, timeout=3)

    # 4. Làm sạch đường dẫn nguồn
    raw_ref = data.get("referrer_path") or request.META.get("HTTP_REFERER", "")
    referrer_path = _sanitize_referrer_path(raw_ref)

    # 5. Ghi nhận ClickEvent
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
