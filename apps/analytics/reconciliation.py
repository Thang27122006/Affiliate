import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from .models import AffiliateConversion, ConversionStatusChoices
from apps.catalog.models import Product
from apps.content.models import Article
from apps.affiliates.models import Merchant

logger = logging.getLogger(__name__)

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

REQUIRED_CSV_FIELDS = {
    "program",
    "transaction_id",
    "transaction_time",
    "status",
    "commission",
    "currency",
}


def parse_reconciliation_csv(file_content_or_obj, dry_run=False):
    """
    Xử lý và nhập dữ liệu đối soát từ file CSV của đối tác tiếp thị liên kết:
    
    NGUYÊN TẮC QUẢN LÝ DỮ LIỆU:
    1. Kiểm tra toàn bộ dữ liệu trước khi nhập; báo cáo chi tiết từng dòng lỗi.
    2. Sử dụng transaction.atomic để đảm bảo tính toàn vẹn (không lưu dở dang nếu có lỗi cấu trúc).
    3. Idempotent: Import lại cùng file hoặc file cập nhật mới sẽ cập nhật bản ghi hiện có
       hoặc bỏ qua nếu không đổi, tuyệt đối KHÔNG nhân đôi số liệu doanh thu.
    4. Định danh bản ghi duy nhất bởi: (program_name, external_transaction_id, external_order_item_id)
       để không gộp nhầm các mặt hàng khác nhau trong cùng một đơn hàng.
    5. Chỉ gắn kết giao dịch với sản phẩm hoặc bài viết khi có mã tracking rõ ràng;
       tuyệt đối không suy đoán theo thời gian gần nhau.
    6. Tuyệt đối không yêu cầu hoặc lưu trữ thông tin cá nhân của người mua hàng.
    
    Trả về dict:
    {
        "success": bool,
        "total_rows": int,
        "created_count": int,
        "updated_count": int,
        "errors": list[{"row": int, "reason": str}],
        "imported_records": list[AffiliateConversion],
    }
    """
    # 1. Đọc nội dung file text
    if hasattr(file_content_or_obj, "read"):
        raw_bytes = file_content_or_obj.read()
        if isinstance(raw_bytes, str):
            content = raw_bytes
        else:
            try:
                content = raw_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                content = raw_bytes.decode("utf-8", errors="replace")
    elif isinstance(file_content_or_obj, bytes):
        try:
            content = file_content_or_obj.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = file_content_or_obj.decode("utf-8", errors="replace")
    else:
        content = str(file_content_or_obj)

    stream = io.StringIO(content.strip())
    reader = csv.reader(stream)

    try:
        header_row = next(reader)
    except StopIteration:
        return {
            "success": False,
            "total_rows": 0,
            "created_count": 0,
            "updated_count": 0,
            "errors": [{"row": 0, "reason": "Tập tin CSV rỗng, không có dữ liệu."}],
            "imported_records": [],
        }

    # Chuẩn hóa tên các cột trong header
    normalized_header = [col.strip().lower() for col in header_row]
    header_map = {col: idx for idx, col in enumerate(normalized_header)}

    # Kiểm tra các cột bắt buộc
    missing_fields = REQUIRED_CSV_FIELDS - set(normalized_header)
    if missing_fields:
        missing_str = ", ".join(sorted(missing_fields))
        return {
            "success": False,
            "total_rows": 0,
            "created_count": 0,
            "updated_count": 0,
            "errors": [
                {
                    "row": 1,
                    "reason": f"Tập tin CSV thiếu các cột bắt buộc: [{missing_str}]. "
                              f"Định dạng chuẩn yêu cầu: program, transaction_id, item_id, "
                              f"transaction_time, status, commission, currency, tracking_code.",
                }
            ],
            "imported_records": [],
        }

    parsed_rows = []
    errors = []
    row_number = 1  # Dòng 1 là header, các dòng sau bắt đầu từ 2

    # Bộ cache phục vụ tra cứu nhanh sản phẩm và bài viết theo tracking_code
    products_by_slug = {p.slug: p for p in Product.objects.all()}
    articles_by_slug = {a.slug: a for a in Article.objects.all()}
    merchants_by_name = {m.name.lower(): m for m in Merchant.objects.all()}

    # 2. Bước kiểm duyệt (Validation) từng dòng dữ liệu
    for row in reader:
        row_number += 1
        # Bỏ qua dòng trống hoàn toàn
        if not row or not any(field.strip() for field in row):
            continue

        def get_field(name, default=""):
            idx = header_map.get(name)
            if idx is not None and idx < len(row):
                return row[idx].strip()
            return default

        program = get_field("program")
        transaction_id = get_field("transaction_id")
        item_id = get_field("item_id", "")
        time_str = get_field("transaction_time")
        status_str = get_field("status").lower()
        commission_str = get_field("commission")
        currency = get_field("currency", "VND").upper()
        tracking_code = get_field("tracking_code", "")

        # Kiểm tra tính đầy đủ của dòng
        if not program:
            errors.append({"row": row_number, "reason": "Cột 'program' không được để trống."})
            continue
        if not transaction_id:
            errors.append({"row": row_number, "reason": "Cột 'transaction_id' không được để trống."})
            continue
        if not time_str:
            errors.append({"row": row_number, "reason": "Cột 'transaction_time' không được để trống."})
            continue

        # Parse thời gian phát sinh giao dịch
        parsed_time = parse_datetime(time_str.replace(" ", "T"))
        if not parsed_time:
            # Thử parse định dạng DD/MM/YYYY HH:MM:SS nếu có
            try:
                from datetime import datetime
                parsed_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                errors.append(
                    {
                        "row": row_number,
                        "reason": f"Thời gian '{time_str}' sai định dạng. Cần dùng: YYYY-MM-DD HH:MM:SS.",
                    }
                )
                continue

        # Gán múi giờ Asia/Ho_Chi_Minh nếu thời gian là naive
        if timezone.is_naive(parsed_time):
            parsed_time = timezone.make_aware(parsed_time, VIETNAM_TZ)

        # Parse trạng thái hoa hồng
        if status_str not in ConversionStatusChoices.values:
            valid_statuses = ", ".join(ConversionStatusChoices.values)
            errors.append(
                {
                    "row": row_number,
                    "reason": f"Trạng thái '{status_str}' không hợp lệ. Phải là một trong: [{valid_statuses}].",
                }
            )
            continue

        # Parse số tiền hoa hồng
        try:
            commission_clean = commission_str.replace(",", "").replace(" ", "")
            commission = Decimal(commission_clean)
            if commission < 0:
                raise ValueError()
        except (InvalidOperation, ValueError):
            errors.append(
                {
                    "row": row_number,
                    "reason": f"Số tiền hoa hồng '{commission_str}' không hợp lệ (phải là số >= 0).",
                }
            )
            continue

        # Đối chiếu sản phẩm / bài viết khi có tracking_code rõ ràng
        matched_product = None
        matched_article = None

        if tracking_code:
            code_lower = tracking_code.lower().strip()
            # Quy ước tiền tố: prod-<slug> hoặc art-<slug>
            if code_lower.startswith("prod-"):
                prod_slug = code_lower[5:]
                matched_product = products_by_slug.get(prod_slug)
            elif code_lower.startswith("art-"):
                art_slug = code_lower[4:]
                matched_article = articles_by_slug.get(art_slug)
            else:
                # Tìm trực tiếp theo slug nếu không có tiền tố
                matched_product = products_by_slug.get(code_lower)
                if not matched_product:
                    matched_article = articles_by_slug.get(code_lower)

        # Tìm merchant tương ứng trong hệ thống nếu có
        merchant = merchants_by_name.get(program.lower())

        parsed_rows.append(
            {
                "program_name": program,
                "merchant": merchant,
                "external_transaction_id": transaction_id,
                "external_order_item_id": item_id,
                "transaction_time": parsed_time,
                "status": status_str,
                "commission_amount": commission,
                "currency": currency,
                "tracking_code": tracking_code,
                "matched_product": matched_product,
                "matched_article": matched_article,
            }
        )

    # Nếu có bất kỳ dòng nào bị lỗi, không thực hiện import để bảo vệ tính toàn vẹn dữ liệu
    if errors:
        return {
            "success": False,
            "total_rows": len(parsed_rows) + len(errors),
            "created_count": 0,
            "updated_count": 0,
            "errors": errors,
            "imported_records": [],
        }

    if dry_run:
        return {
            "success": True,
            "total_rows": len(parsed_rows),
            "created_count": len(parsed_rows),
            "updated_count": 0,
            "errors": [],
            "imported_records": [],
        }

    # 3. Bước lưu vào cơ sở dữ liệu trong Transaction Atomic
    created_count = 0
    updated_count = 0
    imported_records = []

    with transaction.atomic():
        for item in parsed_rows:
            obj, created = AffiliateConversion.objects.update_or_create(
                program_name=item["program_name"],
                external_transaction_id=item["external_transaction_id"],
                external_order_item_id=item["external_order_item_id"],
                defaults={
                    "merchant": item["merchant"],
                    "transaction_time": item["transaction_time"],
                    "status": item["status"],
                    "commission_amount": item["commission_amount"],
                    "currency": item["currency"],
                    "tracking_code": item["tracking_code"],
                    "matched_product": item["matched_product"],
                    "matched_article": item["matched_article"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            imported_records.append(obj)

    return {
        "success": True,
        "total_rows": len(parsed_rows),
        "created_count": created_count,
        "updated_count": updated_count,
        "errors": [],
        "imported_records": imported_records,
    }
