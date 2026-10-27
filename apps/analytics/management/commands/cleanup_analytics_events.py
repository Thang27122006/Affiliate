from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.analytics.models import ClickEvent, PageView


class Command(BaseCommand):
    help = (
        "Dọn dẹp các sự kiện kỹ thuật cũ (PageView, ClickEvent) theo chính sách lưu giữ dữ liệu. "
        "Dữ liệu đối soát tài chính (AffiliateConversion) được giữ lại nguyên vẹn."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Số ngày lưu giữ sự kiện. Mọi sự kiện cũ hơn N ngày sẽ được xử lý (mặc định: 90 ngày).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Chế độ chạy thử nghiệm (dry-run): Chỉ quét và thống kê số bản ghi mà không xóa thật trong database.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        if days <= 0:
            self.stdout.write(self.style.ERROR("Lỗi: Số ngày lưu giữ (--days) phải lớn hơn 0."))
            return

        cutoff_date = timezone.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%d/%m/%Y %H:%M:%S UTC")

        self.stdout.write(
            f"[*] Bắt đầu quét dữ liệu sự kiện trước thời điểm: {cutoff_str} (cũ hơn {days} ngày)..."
        )

        # Đếm số bản ghi cũ
        old_page_views = PageView.objects.filter(created_at__lt=cutoff_date)
        old_clicks = ClickEvent.objects.filter(created_at__lt=cutoff_date)

        page_views_count = old_page_views.count()
        clicks_count = old_clicks.count()
        total_count = page_views_count + clicks_count

        if dry_run:
            self.stdout.write(self.style.WARNING("--- [CHẾ ĐỘ DRY-RUN (CHẠY THỬ)] ---"))
            self.stdout.write(f"- Lượt xem trang (PageView) sẽ bị xóa: {page_views_count:,} bản ghi")
            self.stdout.write(f"- Lượt bấm đối tác (ClickEvent) sẽ bị xóa: {clicks_count:,} bản ghi")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Tổng cộng {total_count:,} bản ghi sự kiện cũ đủ điều kiện dọn dẹp. "
                    "Không có dữ liệu nào bị thay đổi do đang bật cờ --dry-run."
                )
            )
            return

        # Thực hiện xóa thật
        deleted_views, _ = old_page_views.delete()
        deleted_clicks, _ = old_clicks.delete()

        self.stdout.write(self.style.SUCCESS(
            f"[✓] Dọn dẹp hoàn tất thành công!\n"
            f"- Đã xóa {deleted_views:,} bản ghi PageView cũ.\n"
            f"- Đã xóa {deleted_clicks:,} bản ghi ClickEvent cũ.\n"
            f"- Dữ liệu đối soát tài chính (AffiliateConversion) được bảo toàn nguyên vẹn."
        ))
