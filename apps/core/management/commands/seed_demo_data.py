from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.catalog.models import (
    Category,
    Product,
    SpecificationDefinition,
    ProductSpecification,
    StatusChoices,
    DataTypeChoices,
)
from apps.content.models import Article, ArticleTypeChoices
from apps.affiliates.models import Merchant, Offer

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Khởi tạo dữ liệu mẫu (Demo Data) phục vụ thử nghiệm hệ thống. "
        "Tất cả dữ liệu mẫu đều được đánh dấu is_demo=True và mặc định ở trạng thái Bản Nháp (draft). "
        "Lệnh chạy lặp lại an toàn (idempotent), không tạo trùng lặp và không làm mất dữ liệu thực."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean-demo",
            action="store_true",
            help="Chỉ xóa sạch các bản ghi có cờ is_demo=True trước khi tạo lại (an toàn tuyệt đối với dữ liệu thực).",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Thiết lập trạng thái xuất bản (published) cho dữ liệu demo để kiểm tra giao diện công khai.",
        )

    def handle(self, *args, **options):
        if options["clean_demo"]:
            self.stdout.write(self.style.WARNING("Đang dọn dẹp các dữ liệu demo cũ..."))
            Offer.objects.filter(is_demo=True).delete()
            Article.objects.filter(is_demo=True).delete()
            ProductSpecification.objects.filter(product__is_demo=True).delete()
            Product.objects.filter(is_demo=True).delete()
            SpecificationDefinition.objects.filter(category__is_demo=True).delete()
            Category.objects.filter(is_demo=True).delete()
            Merchant.objects.filter(is_demo=True).delete()
            self.stdout.write(self.style.SUCCESS("Đã dọn dẹp dữ liệu demo."))

        target_status = StatusChoices.PUBLISHED if options.get("publish") else StatusChoices.DRAFT
        pub_time = timezone.now() if options.get("publish") else None

        self.stdout.write(f"Bắt đầu khởi tạo dữ liệu demo (Trạng thái: {target_status})...")

        # 1. Tác giả demo
        author, created = User.objects.get_or_create(
            username="editor_demo",
            defaults={
                "email": "editor_demo@gocphukien.local",
                "is_staff": True,
                "first_name": "Biên tập viên",
                "last_name": "Demo",
            },
        )
        if created:
            author.set_password("DemoPassword123!")
            author.save()
            self.stdout.write(f"Đã tạo tài khoản biên tập demo: {author.username}")

        # 2. Danh mục ban đầu (Bàn phím, Chuột, Giá đỡ)
        cat_data = [
            {
                "name": "Bàn phím",
                "slug": "ban-phim",
                "display_order": 1,
                "description": "Bàn phím cơ giá sinh viên, bàn phím Bluetooth mỏng nhẹ di động.",
            },
            {
                "name": "Chuột máy tính",
                "slug": "chuot-may-tinh",
                "display_order": 2,
                "description": "Chuột văn phòng silent, chuột công thái học cho học tập và làm việc.",
            },
            {
                "name": "Giá đỡ laptop",
                "slug": "gia-do-laptop",
                "display_order": 3,
                "description": "Giá đỡ nhôm tản nhiệt, nâng góc nhìn bảo vệ cổ vai gáy khi ngồi học.",
            },
        ]

        categories = {}
        for c in cat_data:
            cat_obj, created = Category.objects.get_or_create(
                slug=c["slug"],
                defaults={
                    "name": c["name"],
                    "description": c["description"],
                    "display_order": c["display_order"],
                    "status": target_status,
                    "is_demo": True,
                },
            )
            cat_obj.display_order = c["display_order"]
            if options.get("publish"):
                cat_obj.status = target_status
            cat_obj.save()
            categories[c["slug"]] = cat_obj
            self.stdout.write(f" - Danh mục: {cat_obj.name} (Thứ tự: {cat_obj.display_order})")

        # 3. Định nghĩa thông số (SpecificationDefinition)
        specs_data = [
            # Chuột
            {"cat": "chuot-may-tinh", "name": "Độ phân giải DPI", "key": "dpi_max", "unit": "DPI", "data_type": DataTypeChoices.NUMBER, "order": 1},
            {"cat": "chuot-may-tinh", "name": "Kiểu kết nối", "key": "connection_type", "unit": "", "data_type": DataTypeChoices.TEXT, "order": 2},
            {"cat": "chuot-may-tinh", "name": "Trọng lượng", "key": "weight", "unit": "g", "data_type": DataTypeChoices.NUMBER, "order": 3},
            {"cat": "chuot-may-tinh", "name": "Nút bấm êm (Silent)", "key": "is_silent", "unit": "", "data_type": DataTypeChoices.BOOLEAN, "order": 4},
            # Bàn phím
            {"cat": "ban-phim", "name": "Bố cục phím (Layout)", "key": "layout", "unit": "", "data_type": DataTypeChoices.TEXT, "order": 1},
            {"cat": "ban-phim", "name": "Loại Switch", "key": "switch_type", "unit": "", "data_type": DataTypeChoices.TEXT, "order": 2},
            {"cat": "ban-phim", "name": "Kết nối không dây", "key": "is_wireless", "unit": "", "data_type": DataTypeChoices.BOOLEAN, "order": 3},
            # Giá đỡ laptop
            {"cat": "gia-do-laptop", "name": "Chất liệu", "key": "material", "unit": "", "data_type": DataTypeChoices.TEXT, "order": 1},
            {"cat": "gia-do-laptop", "name": "Kích thước laptop hỗ trợ", "key": "supported_size", "unit": "inch", "data_type": DataTypeChoices.TEXT, "order": 2},
            {"cat": "gia-do-laptop", "name": "Số nấc chỉnh độ cao", "key": "adjustment_levels", "unit": "nấc", "data_type": DataTypeChoices.NUMBER, "order": 3},
        ]

        spec_defs = {}
        for s in specs_data:
            cat = categories[s["cat"]]
            s_obj, _ = SpecificationDefinition.objects.get_or_create(
                category=cat,
                key=s["key"],
                defaults={
                    "name": s["name"],
                    "unit": s["unit"],
                    "data_type": s["data_type"],
                    "display_order": s["order"],
                },
            )
            spec_defs[(s["cat"], s["key"])] = s_obj

        # 4. Sản phẩm demo (Product)
        products_data = [
            # Chuột máy tính
            {
                "cat": "chuot-may-tinh",
                "name": "Chuột không dây Pebble M350",
                "brand": "Logitech",
                "slug": "logitech-pebble-m350",
                "model": "M350",
                "short_description": "Chuột không dây mỏng nhẹ, nút bấm silent êm ái thích hợp học thư viện.",
                "specs": [
                    ("dpi_max", "1000"),
                    ("connection_type", "Bluetooth & 2.4GHz USB"),
                    ("weight", "100"),
                    ("is_silent", "Có"),
                ],
            },
            {
                "cat": "chuot-may-tinh",
                "name": "Chuột công thái học M331 Silent Plus",
                "brand": "Logitech",
                "slug": "logitech-m331-silent-plus",
                "model": "M331",
                "short_description": "Chuột công thái học tay phải, giảm hơn 90% tiếng ồn click, pin bền bỉ 24 tháng.",
                "specs": [
                    ("dpi_max", "1000"),
                    ("connection_type", "USB Receiver 2.4GHz"),
                    ("weight", "101"),
                    ("is_silent", "Có"),
                ],
            },
            {
                "cat": "chuot-may-tinh",
                "name": "Chuột không dây EM901X Wireless RGB",
                "brand": "DareU",
                "slug": "dareu-em901x-wireless-rgb",
                "model": "EM901X",
                "short_description": "Chuột gaming & học tập không dây kèm dock sạc RGB tiện lợi, trọng lượng đầm tay.",
                "specs": [
                    ("dpi_max", "6000"),
                    ("connection_type", "Type-C & 2.4GHz Wireless"),
                    ("weight", "85"),
                    ("is_silent", "Không"),
                ],
            },
            # Bàn phím
            {
                "cat": "ban-phim",
                "name": "Bàn phím cơ EK387 RGB",
                "brand": "E-Dra",
                "slug": "e-dra-ek387-rgb",
                "model": "EK387",
                "short_description": "Bàn phím cơ Tenkeyless quốc dân cho sinh viên, switch quang cơ bền bỉ.",
                "specs": [
                    ("layout", "TKL 87 phím"),
                    ("switch_type", "Outemu Blue/Red/Brown"),
                    ("is_wireless", "Không (Dây USB Type-C)"),
                ],
            },
            {
                "cat": "ban-phim",
                "name": "Bàn phím cơ EK87 Multi-Led",
                "brand": "DareU",
                "slug": "dareu-ek87-multi-led",
                "model": "EK87",
                "short_description": "Bàn phím cơ giá rẻ cảm giác gõ tốt, led cầu vồng phân vùng bắt mắt.",
                "specs": [
                    ("layout", "TKL 87 phím"),
                    ("switch_type", "D-Switch Brown/Red"),
                    ("is_wireless", "Không (Cáp USB liền 1.8m)"),
                ],
            },
            {
                "cat": "ban-phim",
                "name": "Bàn phím không dây K380 Multi-Device",
                "brand": "Logitech",
                "slug": "logitech-k380-multi-device",
                "model": "K380",
                "short_description": "Bàn phím Bluetooth không dây mỏng nhẹ, phím tròn êm ái, chuyển đổi 3 thiết bị.",
                "specs": [
                    ("layout", "Compact 79 phím tròn"),
                    ("switch_type", "Scissor phím cắt kéo siêu êm"),
                    ("is_wireless", "Có (Bluetooth 3 thiết bị)"),
                ],
            },
            # Giá đỡ laptop
            {
                "cat": "gia-do-laptop",
                "name": "Giá đỡ nhôm N3",
                "brand": "OEM",
                "slug": "gia-do-nhom-gap-gon-n3",
                "model": "N3-Alloy",
                "short_description": "Giá đỡ gập gọn hợp kim nhôm 6 nấc chỉnh độ cao, tản nhiệt tốt cho laptop 11-15.6 inch.",
                "specs": [
                    ("material", "Hợp kim nhôm & Silicone chống trượt"),
                    ("supported_size", "11 - 15.6"),
                    ("adjustment_levels", "6"),
                ],
            },
            {
                "cat": "gia-do-laptop",
                "name": "Giá đỡ nhôm Orico LST-T1",
                "brand": "Orico",
                "slug": "gia-do-nhom-orico-lst-t1",
                "model": "LST-T1",
                "short_description": "Giá đỡ laptop cao cấp bằng nhôm nguyên khối, trục kép xoay góc linh hoạt chống mỏi cổ.",
                "specs": [
                    ("material", "Nhôm nguyên khối phay xước"),
                    ("supported_size", "11 - 17"),
                    ("adjustment_levels", "Vô cấp (trục kép)"),
                ],
            },
        ]

        products = {}
        for p in products_data:
            cat = categories[p["cat"]]
            prod_obj, prod_created = Product.objects.get_or_create(
                slug=p["slug"],
                defaults={
                    "category": cat,
                    "name": p["name"],
                    "brand": p["brand"],
                    "model": p["model"],
                    "short_description": p["short_description"],
                    "status": target_status,
                    "is_demo": True,
                },
            )
            if not prod_created:
                prod_obj.name = p["name"]
                prod_obj.brand = p["brand"]
                prod_obj.model = p["model"]
                prod_obj.short_description = p["short_description"]
                if options.get("publish"):
                    prod_obj.status = target_status
                prod_obj.save()
            products[p["slug"]] = prod_obj
            self.stdout.write(f" - Sản phẩm: {prod_obj}")

            # Gán thông số
            for key, val in p["specs"]:
                spec_def = spec_defs.get((p["cat"], key))
                if spec_def:
                    ProductSpecification.objects.get_or_create(
                        product=prod_obj,
                        specification_definition=spec_def,
                        defaults={"value": val},
                    )

        # 5. Nhà bán hàng demo (Merchant)
        merchants_data = [
            {
                "name": "Shopee Vietnam",
                "slug": "shopee-vn",
                "website": "https://shopee.vn",
                "hostnames": "shopee.vn, s.shopee.vn",
            },
            {
                "name": "Tiki",
                "slug": "tiki-vn",
                "website": "https://tiki.vn",
                "hostnames": "tiki.vn, ti.ki",
            },
        ]

        merchants = {}
        for m in merchants_data:
            m_obj, _ = Merchant.objects.get_or_create(
                slug=m["slug"],
                defaults={
                    "name": m["name"],
                    "website": m["website"],
                    "allowed_hostnames": m["hostnames"],
                    "is_active": True,
                    "is_demo": True,
                },
            )
            merchants[m["slug"]] = m_obj
            self.stdout.write(f" - Nơi bán: {m_obj.name}")

        # 6. Offer mẫu (minh họa rõ ràng là link demo, không giả mạo)
        offers_data = [
            {
                "product": products["logitech-pebble-m350"],
                "merchant": merchants["shopee-vn"],
                "url": "https://shopee.vn/demo-san-pham-logitech-m350-placeholder",
                "price": Decimal("350000"),
            },
            {
                "product": products["logitech-m331-silent-plus"],
                "merchant": merchants["tiki-vn"],
                "url": "https://tiki.vn/demo-san-pham-logitech-m331-placeholder",
                "price": Decimal("320000"),
            },
            {
                "product": products["dareu-em901x-wireless-rgb"],
                "merchant": merchants["shopee-vn"],
                "url": "https://shopee.vn/demo-san-pham-dareu-em901x-placeholder",
                "price": Decimal("490000"),
            },
            {
                "product": products["e-dra-ek387-rgb"],
                "merchant": merchants["tiki-vn"],
                "url": "https://tiki.vn/demo-san-pham-e-dra-ek387-placeholder",
                "price": Decimal("590000"),
            },
            {
                "product": products["dareu-ek87-multi-led"],
                "merchant": merchants["shopee-vn"],
                "url": "https://shopee.vn/demo-san-pham-dareu-ek87-placeholder",
                "price": Decimal("450000"),
            },
            {
                "product": products["logitech-k380-multi-device"],
                "merchant": merchants["tiki-vn"],
                "url": "https://tiki.vn/demo-san-pham-logitech-k380-placeholder",
                "price": Decimal("620000"),
            },
            {
                "product": products["gia-do-nhom-gap-gon-n3"],
                "merchant": merchants["shopee-vn"],
                "url": "https://shopee.vn/demo-gia-do-n3-placeholder",
                "price": None,  # Mẫu sản phẩm chưa có giá theo yêu cầu đề bài
            },
            {
                "product": products["gia-do-nhom-orico-lst-t1"],
                "merchant": merchants["tiki-vn"],
                "url": "https://tiki.vn/demo-gia-do-orico-lst-t1-placeholder",
                "price": Decimal("390000"),
            },
        ]

        for o in offers_data:
            Offer.objects.get_or_create(
                product=o["product"],
                merchant=o["merchant"],
                affiliate_url=o["url"],
                defaults={
                    "price": o["price"],
                    "currency": "VND",
                    "price_checked_at": timezone.now(),
                    "is_active": True,
                    "is_demo": True,
                },
            )

        # 7. Bài viết mẫu (Article) - Đảm bảo tính trung thực: Không giả mạo trải nghiệm
        article_slug = "demo-tieu-chi-chon-phu-kien-sinh-vien"
        article_content = """## Lựa chọn phụ kiện học tập thông minh cho sinh viên

Khi trang bị góc học tập trong phòng trọ hoặc ký túc xá, sinh viên thường đối mặt với ngân sách hạn hẹp nhưng vẫn mong muốn có các công cụ bền bỉ, êm ái để không ảnh hưởng đến người xung quanh.

### 1. Chuột máy tính: Ưu tiên chống ồn
Trong thư viện hoặc phòng ký túc xá ban đêm, tiếng click chuột truyền thống dễ gây khó chịu. Những dòng chuột trang bị switch silent như *Logitech Pebble M350* mang lại sự yên tĩnh tối đa.

### 2. Bàn phím: Độ nảy và bảo vệ cổ tay
Gõ tài liệu và làm bài tập lớn trong nhiều giờ đòi hỏi hành trình phím vừa phải và độ phản hồi tốt.

### 3. Giá đỡ laptop: Cải thiện tư thế công thái học
Màn hình laptop quá thấp khiến sinh viên phải cúi gập cổ liên tục. Một chiếc giá đỡ nâng màn hình ngang tầm mắt là khoản đầu tư sức khỏe cần thiết nhất.
"""
        article, art_created = Article.objects.get_or_create(
            slug=article_slug,
            defaults={
                "title": "[Demo] Hướng dẫn chọn combo phụ kiện học tập tối ưu cho sinh viên",
                "summary": "Tổng hợp các tiêu chí cần lưu ý khi sinh viên đầu tư chuột, bàn phím và giá đỡ laptop.",
                "content": article_content,
                "article_type": ArticleTypeChoices.BUYING_GUIDE,
                "author": author,
                "status": target_status,
                "published_at": pub_time,
                "is_demo": True,
                # Tuyệt đối trung thực: bài viết demo tổng hợp, không giả mạo trải nghiệm thực tế
                "is_hands_on_experience": False,
                "testing_methodology": "Phân tích tài liệu kỹ thuật từ nhà sản xuất và khảo sát nhu cầu sinh viên.",
                "testing_duration": "Khảo sát tài liệu trong 1 tuần.",
                "information_source": "Trang thông số kỹ thuật chính hãng Logitech, E-Dra.",
            },
        )
        if not art_created and options.get("publish"):
            article.status = target_status
            article.published_at = pub_time
            article.save()

        article.products.add(
            products["logitech-pebble-m350"],
            products["e-dra-ek387-rgb"],
            products["gia-do-nhom-gap-gon-n3"],
        )
        self.stdout.write(f" - Bài viết: {article.title}")

        self.stdout.write(self.style.SUCCESS("✓ Khởi tạo dữ liệu mẫu hoàn tất thành công!"))
