import logging
from urllib.parse import urlsplit
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.http import require_GET
from .models import Offer, LinkModeChoices
from apps.analytics.models import ClickEvent

logger = logging.getLogger(__name__)


def _sanitize_referrer_path(raw_ref):
    """
    Chuẩn hóa và làm sạch đường dẫn trang nguồn:
    - Chỉ trích xuất phần path (ví dụ: /san-pham/chuot-m350/).
    - Loại bỏ toàn bộ query parameters hoặc fragment có thể chứa thông tin nhạy cảm.
    - Giới hạn độ dài tối đa 500 ký tự.
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


@require_GET
def redirect_offer_view(request, offer_id):
    """
    Chuyển hướng nội bộ an toàn tới nơi bán (Internal Affiliate Redirect):
    
    NGUYÊN TẮC AN TOÀN TUYỆT ĐỐI:
    1. Chống Open Redirect: Chỉ nhận 'offer_id' (số nguyên) từ URL pattern; tuyệt đối
       không nhận tham số URL đích tùy ý từ query string hoặc request headers.
    2. Chống SSRF: Backend tuyệt đối không gửi request HTTP nào tới URL đích.
    3. Kiểm duyệt trạng thái: Chỉ cho phép chuyển hướng nếu Offer active, Merchant active,
       Sản phẩm đã xuất bản (status='published') và Danh mục đã xuất bản.
    4. Kiểm duyệt URL: Bắt buộc URL phải là HTTPS và thuộc danh sách hostname đã duyệt của Merchant.
    5. Ghi nhận lượt bấm chịu lỗi: Sự cố ghi nhận ClickEvent không được làm gián đoạn chuyển hướng.
    """
    offer = get_object_or_404(
        Offer.objects.select_related("merchant", "product__category"),
        id=offer_id,
    )

    # 1. Kiểm tra trạng thái hoạt động của Offer và Merchant
    if not offer.is_active or not offer.merchant.is_active:
        raise Http404("Nơi bán liên kết này hiện đang tạm dừng hoạt động.")

    # 2. Kiểm tra trạng thái xuất bản của Sản phẩm và Danh mục
    product = offer.product
    category = product.category
    if product.status != "published" or (category and category.status != "published"):
        raise Http404("Sản phẩm hoặc danh mục này chưa được xuất bản công khai.")

    # 3. Kiểm tra an toàn URL lần cuối trước khi chuyển hướng
    if not offer.merchant.is_url_allowed(offer.affiliate_url):
        logger.warning(
            f"Bị chặn chuyển hướng: Offer #{offer.id} có affiliate_url không hợp lệ hoặc "
            f"hostname không thuộc nơi bán {offer.merchant.name}: {offer.affiliate_url}"
        )
        raise Http404("Liên kết nơi bán không hợp lệ hoặc không đáp ứng tiêu chuẩn an toàn.")

    # 4. Ghi nhận lượt bấm ClickEvent (chịu lỗi, không làm gián đoạn người đọc)
    try:
        raw_ref = request.GET.get("ref") or request.META.get("HTTP_REFERER", "")
        referrer_path = _sanitize_referrer_path(raw_ref)

        ClickEvent.objects.create(
            offer=offer,
            link_mode=LinkModeChoices.REDIRECT,
            referrer_path=referrer_path,
        )
    except Exception as exc:
        logger.error(f"Lỗi khi ghi nhận ClickEvent cho Offer #{offer.id}: {exc}", exc_info=True)

    # 5. Chuyển hướng tới URL đối tác chính thức (HTTP 302 Found)
    # Giữ nguyên toàn bộ tham số tracking của URL ban đầu do quản trị viên nhập
    return HttpResponseRedirect(offer.affiliate_url)
