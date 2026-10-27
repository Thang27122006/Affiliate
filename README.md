# Góc Phụ Kiện

> Website đánh giá, so sánh phụ kiện học tập và làm việc dành cho sinh viên, tạo doanh thu từ tiếp thị liên kết (Affiliate Marketing).

---

## 1. Công Nghệ & Môi Trường
- **Python:** 3.14.4
- **Django:** 5.2.18
- **Database:** PostgreSQL (kết nối qua `psycopg 3.3.6`)
- **Frontend:** Django Templates + Semantic HTML5 + Vanilla CSS + Vanilla JS
- **Múi giờ:** `Asia/Ho_Chi_Minh`
- **Ngôn ngữ:** Tiếng Việt (`vi`)

---

## 2. Cấu Trúc Thư Mục
```
Affiliate/
├── .env.example              # Mẫu cấu hình biến môi trường an toàn
├── .gitignore                # Danh sách loại trừ Git (bảo mật .env, cache, venv)
├── docker-compose.yml        # Docker Compose cho PostgreSQL (tuỳ chọn)
├── requirements.txt          # Danh sách thư viện Python với phiên bản cố định
├── manage.py                 # Django management script
├── docs/
│   └── CONVENTIONS.md        # Quy ước kiến trúc và nguyên tắc phát triển
├── config/                   # Cấu hình dự án Django
│   ├── settings/
│   │   ├── base.py           # Cấu hình chung (DB PostgreSQL, App, Localization)
│   │   ├── development.py    # Cấu hình môi trường phát triển
│   │   └── production.py     # Cấu hình môi trường sản xuất
│   ├── urls.py               # Định tuyến chính
│   ├── wsgi.py
│   └── asgi.py
├── apps/                     # Các module nghiệp vụ độc lập
│   ├── core/                 # Trang chủ, layouts, models cơ sở, health check
│   ├── catalog/              # Danh mục sản phẩm (chuột, bàn phím, giá đỡ laptop)
│   ├── content/              # Bài viết đánh giá, cẩm nang chọn mua
│   ├── affiliates/           # Quản lý đối tác affiliate, tracking links
│   └── analytics/            # Thống kê lượt click, phân tích số liệu
├── templates/                # Giao diện HTML (Django Templates)
│   ├── base.html             # Layout chuẩn dùng chung
│   └── core/
│       └── home.html         # Trang chủ tối giản xác nhận hoạt động
├── static/                   # Static assets
│   ├── css/style.css         # Hệ thống thiết kế Vanilla CSS hiện đại
│   └── js/main.js            # JavaScript thuần
└── media/                    # Thư mục lưu trữ media tải lên
```

---

## 3. Hướng Dẫn Cài Đặt & Khởi Chạy

### Bước 1: Khởi tạo Virtual Environment và Cài đặt Thư viện
```bash
# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate

# Cài đặt các thư viện bắt buộc
pip install -r requirements.txt
```

### Bước 2: Cấu hình Biến môi trường (.env)
Sao chép file mẫu `.env.example` thành `.env` và cập nhật thông tin kết nối PostgreSQL:
```bash
cp .env.example .env
```
Nội dung file `.env`:
```ini
DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
DJANGO_SETTINGS_MODULE=config.settings.development

# Cấu hình PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=gocphukien
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

TIME_ZONE=Asia/Ho_Chi_Minh
LANGUAGE_CODE=vi
```

### Bước 3: Chuẩn bị Cơ sở dữ liệu PostgreSQL
Bạn có thể sử dụng PostgreSQL cài sẵn trên máy cục bộ hoặc qua Docker Compose:

#### Cách 1: Sử dụng PostgreSQL cài đặt cục bộ trên máy
```bash
# Tạo cơ sở dữ liệu 'gocphukien'
psql -h localhost -U postgres -c "CREATE DATABASE gocphukien;"
```

#### Cách 2: Sử dụng Docker Compose (Tuỳ chọn)
```bash
# Khởi chạy container PostgreSQL
docker-compose up -d
```

### Bước 4: Kích hoạt Extension unaccent trên PostgreSQL
Hệ thống sử dụng extension `unaccent` của PostgreSQL để hỗ trợ tìm kiếm tiếng Việt không dấu (ví dụ: gõ `chuot` vẫn tìm ra `Chuột máy tính`):
```bash
# Kích hoạt extension unaccent trong cơ sở dữ liệu (kết nối qua TCP -h localhost, mật khẩu mặc định là 123)
psql -h localhost -U postgres -d gocphukien -c "CREATE EXTENSION IF NOT EXISTS unaccent;"

# (Khuyến nghị cho test database) Kích hoạt trên template1 để mọi test db tự động có unaccent:
psql -h localhost -U postgres -d template1 -c "CREATE EXTENSION IF NOT EXISTS unaccent;"
```

### Bước 5: Chạy Migration và Tạo Superuser
```bash
# Thực hiện migrate cơ sở dữ liệu (đã bao gồm migration UnaccentExtension)
python manage.py migrate

# Tạo tài khoản quản trị viên truy cập Django Admin
python manage.py createsuperuser
```

### Bước 6: Nạp Dữ liệu Mẫu (Demo Data)
Hệ thống cung cấp management command độc lập để nạp dữ liệu mẫu cho chuột máy tính, bàn phím và giá đỡ laptop:
```bash
# Khởi tạo dữ liệu mẫu và tự động xuất bản (published) để trải nghiệm tìm kiếm, lọc và so sánh:
python manage.py seed_demo_data --publish

# (Tùy chọn) Xóa sạch dữ liệu mẫu demo cũ và nạp lại
python manage.py seed_demo_data --clean-demo --publish
```

### Bước 7: Kiểm tra Hệ thống & Khởi chạy Server
```bash
# Chạy system check của Django
python manage.py check

# Khởi chạy máy chủ phát triển
python manage.py runserver
```

Truy cập:
- **Trang chủ:** `http://127.0.0.1:8000/`
- **Tất cả sản phẩm & Bộ lọc:** `http://127.0.0.1:8000/san-pham/`
- **So sánh sản phẩm:** `http://127.0.0.1:8000/so-sanh/`
- **Tìm kiếm:** `http://127.0.0.1:8000/tim-kiem/?q=chuot`
- **Quản trị Django Admin:** `http://127.0.0.1:8000/admin/`
- **Kiểm tra trạng thái (Health Check):** `http://127.0.0.1:8000/health/`

---

## 4. Hướng Dẫn Tính Năng & Quy Tắc Nghiệp Vụ

### 1. Tìm Kiếm (Search)
- **Phạm vi tra cứu:**
  - Sản phẩm: tìm kiếm theo Tên (`name`), Thương hiệu (`brand`), Mã model (`model`).
  - Bài viết: tìm kiếm theo Tiêu đề (`title`) và Tóm tắt (`summary`).
- **Phân tách kết quả:** Giao diện chia rõ ràng thành 2 khối riêng biệt: "Sản Phẩm Phù Hợp" và "Bài Viết & Đánh Giá Phù Hợp".
- **Không dấu & Hoa/Thường:** Hỗ trợ tìm kiếm tiếng Việt không dấu (`chuot` -> `Chuột`, `ban phim` -> `Bàn phím`) nhờ extension `unaccent` và lookup `__unaccent__icontains` trên PostgreSQL. Tự động fallback sang `__icontains` nếu không dùng PostgreSQL.
- **Bảo mật & Chuỗi an toàn:**
  - Không nối chuỗi SQL thô; sử dụng 100% Django ORM parameterized queries.
  - Chuỗi rỗng hoặc chỉ có khoảng trắng được xử lý thân thiện, nhắc người dùng nhập từ khóa.
  - Đầu vào quá dài được tự động làm sạch và cắt gọn về 120 ký tự, hiển thị thông báo nhẹ nhàng cho người dùng.
- **Loại trừ dữ liệu nháp:** Chỉ hiển thị sản phẩm và bài viết đã xuất bản (`PUBLISHED`), loại bỏ bài viết hẹn giờ ở tương lai.

### 2. Bộ Lọc & Sắp Xếp (Filtering & Sorting)
- **Tiêu chí lọc:** Danh mục, thương hiệu, khoảng giá tham khảo (`under_300`, `300_700`, `700_1500`, `above_1500`, hoặc tùy chỉnh `price_min`, `price_max`).
- **Quy tắc giá tham khảo:**
  - Mức giá được dùng để lọc và sắp xếp là **giá thấp nhất ghi nhận từ các Offer đang hoạt động** (`min_price = Min("offers__price", filter=Q(offers__is_active=True))`).
  - *Mô tả minh bạch trên giao diện:* Đây không phải giá thị trường theo thời gian thực và có thể biến động tùy đối tác.
- **Xử lý sản phẩm chưa có giá:**
  - Sản phẩm chưa có nơi bán hiển thị "Chưa có giá" và được xử lý riêng biệt.
  - Tuyệt đối **không coi là 0 đồng**; bị loại khỏi các khoảng giá số học cụ thể.
  - Có tùy chọn lọc riêng: "Chưa có giá tham khảo" (`price_range=no_price`).
- **Sắp xếp:**
  - Mới nhất (`newest`)
  - Tên A &rarr; Z (`name_asc`), Tên Z &rarr; A (`name_desc`)
  - Giá tham khảo thấp đến cao (`price_asc`): sử dụng `nulls_last=True` để sản phẩm chưa có giá luôn đứng cuối cùng, không bị nhầm lẫn thành 0đ.
  - Giá tham khảo cao đến thấp (`price_desc`): cũng sử dụng `nulls_last=True`.
- **Trạng thái & Phân trang:**
  - Mọi tham số lọc được lưu trong URL Query String.
  - Template tag `{% url_replace %}` bảo toàn nguyên vẹn tất cả tham số lọc khi chuyển trang phân trang ở phía máy chủ (Server-side pagination).
  - Có nút "Xóa tất cả bộ lọc" và thông báo khi không có sản phẩm nào thỏa mãn.

### 3. So Sánh Sản Phẩm (Comparison)
- **Quy tắc số lượng:** Hỗ trợ so sánh từ 2 đến tối đa 3 sản phẩm cùng danh mục.
- **Kiểm soát tính hợp lệ:**
  - Tự động lọc trùng lặp sản phẩm (deduplicate theo slug). Nếu chỉ còn 1 sản phẩm, yêu cầu chọn tối thiểu 2 sản phẩm.
  - Nếu số lượng > 3 sản phẩm, hệ thống từ chối và yêu cầu bỏ bớt.
  - Nếu các sản phẩm khác danh mục (ví dụ chọn 1 chuột và 1 bàn phím), hệ thống báo lỗi yêu cầu so sánh trong cùng một danh mục.
  - Bỏ qua các sản phẩm bản nháp.
- **Bảng đối chiếu thông số:**
  - Bảng bao gồm: Ảnh đại diện, tên, thương hiệu, model, giá tham khảo thấp nhất, thời điểm kiểm tra giá gần nhất, và danh sách nơi bán đối tác kèm link affiliate có đánh dấu `rel="noopener noreferrer sponsored"`.
  - Toàn bộ thông số kỹ thuật được sắp xếp chuẩn hóa theo đúng thứ tự (`display_order`) từ định nghĩa chung của danh mục (`SpecificationDefinition`).
  - Thuộc tính thiếu của sản phẩm hiển thị "Chưa có thông tin".
- **Responsive trên điện thoại:**
  - Bảng so sánh nằm trong container `overflow-x: auto; -webkit-overflow-scrolling: touch;`, cho phép vuốt ngang mượt mà trên mobile mà không làm tràn (overflow) bề ngang của toàn trang.
- **Nguyên tắc biên tập minh bạch:**
  - Bảng so sánh công khai thông điệp: *Góc Phụ Kiện không tự động suy ra hay khẳng định sản phẩm nào 'tốt nhất' chỉ dựa trên giá rẻ nhất hay thông số lớn hơn.*

---

## 5. Luồng Chuyển Nơi Bán & Ghi Nhận Affiliate An Toàn

### 1. Hai Chế Độ Liên Kết (Link Modes)
Hệ thống hỗ trợ linh hoạt 2 chế độ liên kết cho từng nơi bán (Merchant) và cho phép cấu hình ghi đè theo từng Offer cụ thể:
- **Liên kết trực tiếp (`direct` - Mặc định):**
  - Thẻ `<a>` trên giao diện trỏ thẳng tới URL affiliate của đối tác (`offer.affiliate_url`).
  - **Lý do mặc định:** Nhiều mạng tiếp thị và sàn TMĐT (Shopee, Lazada...) có điều khoản nghiêm ngặt cấm che link (cloaking), cấm ẩn nguồn truy cập hoặc cấm tự động redirect qua trung gian khi chưa được phê duyệt. Mặc định dùng link trực tiếp để đảm bảo tuân thủ 100% điều khoản chiến dịch và tránh bị hủy doanh số.
  - Bảo toàn 100% các tham số tracking của URL do quản trị viên nhập (`utm_source`, `aff_id`, `sub_id`,...).
  - Không tự ý sinh mã affiliate giả lập.
- **Chuyển hướng nội bộ (`redirect`):**
  - Thẻ `<a>` trỏ tới endpoint nội bộ `/go/<offer_id>/`.
  - Server kiểm tra điều kiện xuất bản, tính an toàn của URL và thực hiện HTTP 302 chuyển hướng tới nơi bán.
  - Chỉ kích hoạt khi đã xác minh rõ điều khoản chương trình đối tác cho phép sử dụng internal redirect/short link.

### 2. An Toàn Liên Kết & Phòng Chống Tấn Công (Link Safety)
- **Bắt buộc HTTPS:** Parse URL bằng `urllib.parse.urlsplit`, từ chối mọi URL dùng `http://` hoặc các scheme nguy hiểm (`javascript:`, `data:`, `file:`, `ftp:`).
- **Chặn thông tin đăng nhập trong URL:** Từ chối các URL có chứa credentials dạng `https://user:pass@domain/`.
- **Kiểm tra Hostname nghiêm ngặt (Whitelist Hostname):**
  - Phân tích hostname thực tế của URL, so khớp với danh sách `allowed_hostnames` của Merchant.
  - Chỉ chấp nhận hostname trùng khớp chính xác hoặc là subdomain chuẩn (ví dụ: `s.shopee.vn` hoặc `shopee.vn`).
  - Chặn triệt để các kỹ thuật giả mạo domain (như `shopee.vn.evil.com` hoặc `evil-shopee.vn`).
- **Chống Open Redirect:** Endpoint `/go/<int:offer_id>/` chỉ nhận ID số nguyên của Offer từ URL path. Tuyệt đối không chấp nhận tham số URL đích tùy ý từ query string hay request body của người đọc.
- **Chống Server-Side Request Forgery (SSRF):** Backend không bao giờ thực hiện HTTP request (fetch/download) tới URL đích của nơi bán.
- **Kiểm soát xuất bản:** Ngắt chuyển hướng và trả về HTTP 404 nếu:
  - Offer bị vô hiệu hóa (`is_active=False`) hoặc Merchant bị tạm dừng (`is_active=False`).
  - Sản phẩm liên kết đang ở trạng thái bản nháp (`status != 'published'`).
  - Danh mục sản phẩm đang ở trạng thái bản nháp (`category.status != 'published'`).

### 3. Ghi Nhận Lượt Bấm Có Trách Nhiệm (Click Tracking & Privacy)
- **Bảo vệ quyền riêng tư người đọc:**
  - Tuyệt đối **KHÔNG thu thập địa chỉ IP thô (raw IP)**.
  - Tuyệt đối **KHÔNG thu thập vân tay trình duyệt (fingerprint)** hay cookies định danh người dùng.
  - Chỉ ghi nhận: `Offer`, thời điểm bấm (`created_at`), hình thức (`link_mode`), và đường dẫn trang nguồn nội bộ đã được làm sạch (`referrer_path`).
- **Debounce / Hạn chế spam click tức thời:**
  - Client-side: Debounce 3 giây cho mỗi offer_id để tránh click đúp.
  - Server-side: Session cache throttle trong vòng 3 giây ngăn chặn gửi lặp tức thời.
- **Tính chịu lỗi cao (Fault Tolerance):**
  - Với liên kết trực tiếp: Thẻ `<a>` luôn mang URL thật, `target="_blank"`, `rel="noopener noreferrer sponsored"`. Việc ghi nhận click được gửi bất đồng bộ qua `navigator.sendBeacon` hoặc `fetch(keepalive)`. Nếu người đọc tắt JavaScript, hoặc API gặp lỗi, hoặc adblocker chặn tracking thì **liên kết vẫn mở bình thường, không hề bị cản trở điều hướng**.
  - Với chuyển hướng nội bộ: Nếu database hoặc logging gặp sự cố, luồng redirect tới nơi bán vẫn tiếp tục thành công, không trả về lỗi 500 cho người dùng.
- **Tính chất số liệu:** Thống kê được trình bày rõ ràng là **Số lượt bấm (Clicks)**, không phải số người dùng duy nhất (Unique Visitors); có thể bị ảnh hưởng bởi bot crawl hoặc công cụ chặn theo dõi.

### 4. Giao Diện & Trải Nghiệm Người Đọc (UI/UX)
- **Công khai minh bạch hoa hồng (Affiliate Disclosure):**
  - Thông điệp minh bạch hiển thị rõ ràng tại chân trang (`base.html`) và ngay bên dưới khối giá tham khảo (`product_detail.html`).
  - Khẳng định rõ website có thể nhận hoa hồng nhỏ khi độc giả mua hàng qua liên kết mà **không làm phát sinh thêm bất kỳ chi phí nào** cho độc giả.
- **Phân định rõ ràng nút hành động:**
  - Nút chuyển đến nơi bán mang màu cam nổi bật, nhãn rõ ràng: `🏪 Xem tại [Tên nơi bán] ↗`, mở tab mới với `rel="noopener noreferrer sponsored"`.
  - Phân biệt hoàn toàn với nút "Đọc bài viết &rarr;" hay "Xem thông số chi tiết".
- **Tuyệt đối không dùng Dark Patterns:**
  - Không có popup ép bấm ("Click để lấy mã giảm giá", popup che nội dung).
  - Không tự ý chuyển hướng (auto-redirect) khi người đọc vừa mở trang bài viết.

---

## 6. Báo Cáo Nội Bộ & Đối Soát Tiếp Thị Liên Kết (Admin Analytics & Reconciliation)

### 1. Phân Biệt Nguồn Số Liệu & Giới Hạn Nghiệp Vụ
Hệ thống phân định rạch ròi 2 nhóm số liệu và công khai giới hạn kỹ thuật:
- **Số liệu nội bộ do website đo (Internal Tracking):**
  - Gồm: Lượt xem trang sản phẩm / bài viết (`PageView`) và Lượt bấm đối tác (`ClickEvent`).
  - *Mục đích:* Đo lường mức độ quan tâm của độc giả đối với nội dung và phụ kiện công nghệ.
  - *Giới hạn:* Đây là số lượng sự kiện kỹ thuật (event count), **không phản ánh số người dùng duy nhất (Unique Visitors)**. Dữ liệu có thể bị sai lệch bởi bot crawl của công cụ tìm kiếm hoặc tiện ích chặn quảng cáo/tracking của người đọc.
  - *Tỷ lệ CTR theo sự kiện (Event-based CTR):* Tính bằng `(Clicks / Views) * 100` trong cùng một phạm vi lọc (cùng khoảng ngày, cùng sản phẩm). Ghi rõ trên giao diện đây là tỷ lệ sự kiện, không chia cho 0 khi lượt xem bằng 0.
- **Số liệu đối soát do sàn đối tác ghi nhận (Partner Reconciliation):**
  - Gồm: Mã đơn hàng (`transaction_id`), mã dòng sản phẩm (`item_id`), thời gian đơn, trạng thái và hoa hồng thực tế.
  - *Mục đích:* Đối soát doanh thu thực tế được ghi nhận bởi các sàn (Shopee, Tiki, Lazada, AccessTrade...).
  - *Giới hạn:* Website chưa tích hợp API tự động khi chưa có thông tin xác thực chính thức từ sàn; số liệu được nhập định kỳ qua file CSV nội bộ chuẩn hóa.
  - *Nguyên tắc đối chiếu:* Chỉ gắn kết giao dịch với sản phẩm hoặc bài viết khi có mã tracking (`tracking_code` / `sub_id`) rõ ràng; **tuyệt đối không phỏng đoán theo thời gian phát sinh gần nhau**. Nếu thiếu tracking code, hệ thống không tính tỷ lệ chuyển đổi suy diễn.

### 2. Quy Định Định Dạng CSV Đối Soát & Tính Toàn Vẹn
Tập tin CSV nhập vào hệ thống sử dụng định dạng chuẩn (UTF-8 / UTF-8-sig) với các cột bắt buộc:
`program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code`
- **Khóa định danh duy nhất (Composite Key):** `(program_name, external_transaction_id, external_order_item_id)`:
  - Cho phép phân tách nhiều sản phẩm khác nhau trong cùng một mã đơn hàng (`transaction_id`) mà không bị gộp đè.
  - Đảm bảo tính **Idempotent**: Nhập lại cùng một file hoặc file cập nhật mới sẽ cập nhật trạng thái (ví dụ từ `pending` sang `approved`) hoặc bỏ qua nếu không đổi, **tuyệt đối không nhân đôi số liệu doanh thu**.
- **Giao dịch nguyên tử (Transaction Atomic) & Báo cáo dòng lỗi:**
  - Toàn bộ file được kiểm duyệt trước khi lưu.
  - Nếu có dòng sai định dạng (thiếu cột bắt buộc, ngày sai cú pháp, hoa hồng âm, trạng thái lạ), hệ thống sẽ **rollback toàn bộ và hiển thị bảng chi tiết các dòng bị lỗi kèm lý do cụ thể**.
- **Tập tin CSV mẫu:** Đặt tại [docs/sample_reconciliation.csv](file:///home/tmthang/Affiliate/docs/sample_reconciliation.csv) dùng dữ liệu minh họa (`DEMO_SPX_001`, `SAMPLE_ITEM`), không tự động import vào database.
- **Bảo mật quyền riêng tư:** File đối soát tuyệt đối không chứa hoặc yêu cầu tên, số điện thoại, địa chỉ hay email của người mua hàng.

### 3. Hiển Thị Báo Cáo Dashboard (Staff Only)
- Đường dẫn: `/analytics/dashboard/` và `/analytics/reconciliation/import/`.
- **Phân quyền chặt chẽ:** Chỉ tài khoản có cờ `is_staff=True` mới có quyền truy cập; khách vãng lai và người dùng thường bị chuyển hướng đến trang đăng nhập admin (`HTTP 302`), không làm lộ dữ liệu kinh doanh ra trang công khai.
- **Xử lý Múi giờ nhất quán:** Toàn bộ bộ lọc khoảng ngày (`start_date`, `end_date`) và hiển thị thời gian đều sử dụng chuẩn múi giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- **Phân tách hoa hồng theo trạng thái:**
  - Hoa hồng đã duyệt (`approved`)
  - Hoa hồng chờ duyệt (`pending`)
  - Hoa hồng bị từ chối (`rejected`)
- **Tách biệt đơn vị tiền tệ:** Hệ thống gom nhóm và hiển thị riêng biệt theo từng loại tiền tệ (`VND`, `USD`...), **tuyệt đối không cộng gộp các loại tiền tệ khác nhau thành một tổng**.

### 4. Chính Sách Lưu Giữ & Command Dọn Dẹp Dữ Liệu Cũ
- Dữ liệu sự kiện kỹ thuật (`PageView`, `ClickEvent`) phát sinh liên tục được đề xuất lưu giữ chi tiết trong 90 ngày.
- **Django Management Command:**
  ```bash
  # Chế độ kiểm tra thử nghiệm (không xóa dữ liệu trong database):
  python manage.py cleanup_analytics_events --days=90 --dry-run

  # Chế độ thực thi dọn dẹp thật:
  python manage.py cleanup_analytics_events --days=90
  ```
- **Nguyên tắc an toàn:**
  - Command chỉ xóa các bản ghi sự kiện `PageView` và `ClickEvent` cũ hơn N ngày.
  - Dữ liệu đối soát tài chính `AffiliateConversion` **được bảo toàn nguyên vẹn** phục vụ đối chiếu kế toán và thuế.
  - Command tuyệt đối **không tự động chạy khi triển khai hoặc migrate**.

---

## 7. Kiểm Thử Hệ Thống (Unit Tests)
Dự án bao gồm **92 bài kiểm thử tự động (100% Passed)** bao phủ toàn diện tính đúng đắn và an toàn:
```bash
# Chạy toàn bộ test suite:
python manage.py test

# Chạy riêng nhóm kiểm thử SEO Kỹ thuật & Bảo mật:
python manage.py test apps.core.tests.SEOTechnicalTestCase apps.core.tests.SecurityUploadValidationTestCase
```

**Các nhóm kiểm thử chính (92 tests):**
1. **SEO Kỹ Thuật, Sitemaps & Minh Bạch Dữ Liệu (8 tests):**
   - Kiểm tra `robots.txt` định dạng text/plain, chặn bot ở `/admin/`, `/analytics/`, `/go/`, `/tim-kiem/`, trỏ đúng `Sitemap`.
   - Kiểm tra `sitemap.xml` chỉ chứa nội dung đã xuất bản (Published), loại trừ bản nháp, bài hẹn giờ tương lai và trang kỹ thuật.
   - Kiểm tra Canonical URL động theo domain thực tế từ request, không dùng domain giả lập cố định.
   - Kiểm tra thẻ `noindex, follow` trên trang tìm kiếm (`/tim-kiem/`), so sánh (`/so-sanh/`) và các tổ hợp bộ lọc danh mục/sản phẩm.
   - Kiểm tra nội dung cam kết quyền riêng tư (không lưu IP thô, không fingerprint, không lưu PII người mua).
   - Kiểm tra chính sách sửa sai (Correction Policy) và 3 mẫu cấu trúc bài viết biên tập chuẩn tại `/gioi-thieu/`.
   - Kiểm tra Open Graph (`og:*`), Twitter Cards (`twitter:*`), và Schema `Article`, `BreadcrumbList`.
   - Xác nhận **tuyệt đối không tạo rating, aggregateRating giả** và chưa thêm `Product`/`Offer` schema khi chưa có dữ liệu thời gian thực.
2. **Bảo Mật Tải Lên Hình Ảnh & File Media (5 tests):**
   - Chấp nhận các định dạng ảnh chuẩn: JPG, JPEG, PNG, WEBP.
   - Từ chối tuyệt đối tệp SVG nhằm triệt tiêu nguy cơ tấn công Stored XSS.
   - Từ chối các tệp có đuôi thực thi nguy hiểm (`.php`, `.html`, `.exe`, `.sh`...).
   - Phát hiện và từ chối tệp văn bản giả mạo đuôi ảnh (chống kỹ thuật file polyglot).
   - Chặn các tệp tải lên vượt quá dung lượng cho phép tối đa 5.0MB.
3. **Analytics Dashboard, Permissions & Reconciliation (20 tests):**
   - Kiểm thử bảo mật quyền truy cập (Staff only, từ chối khách vãng lai & user thường).
   - Kiểm thử lọc khoảng ngày theo múi giờ `Asia/Ho_Chi_Minh`, tự động đảo ngày nếu nhập ngược.
   - Kiểm thử tính toán CTR sự kiện và chống lỗi chia cho 0 khi chưa có lượt xem.
   - Kiểm thử ghi nhận `PageView` cho sản phẩm và bài viết, kiểm tra tính chịu lỗi (resilience) khi database gặp sự cố.
   - Kiểm thử import CSV đối soát: Tạo mới bản ghi, import lặp lại không nhân đôi (idempotency), cập nhật trạng thái đơn (pending -> approved), phân biệt nhiều item trong cùng 1 đơn, báo cáo dòng lỗi và transaction rollback.
   - Kiểm thử tách bạch tiền tệ (VND, USD), đối chiếu sản phẩm/bài viết qua tracking code, xác minh không lưu thông tin PII.
   - Kiểm thử management command `cleanup_analytics_events` (chế độ `--dry-run` không xóa, chế độ thực thi xóa đúng hạn và bảo toàn dữ liệu đối soát).
4. **Affiliate Link Safety & Redirect (18 tests):** Bắt buộc HTTPS, giữ nguyên tham số tracking, chặn HTTP/javascript/data/file, chặn URL chứa credentials, chặn hostname giả mạo mạo danh subdomain, kiểm tra 2 chế độ direct/redirect và override, redirect 302 thành công, 404 khi offer/merchant inactive hoặc product/category draft, chống Open Redirect, tính chịu lỗi khi logging thất bại.
5. **Catalog Constraints & Data Integrity (14 tests):** Ràng buộc giá Decimal > 0, chống gán spec sai danh mục, chống trùng spec trên cùng 1 sản phẩm, tự động sinh slug duy nhất chống xung đột, phương thức `get_absolute_url()` chuẩn SEO.
6. **Bộ lọc & Sắp xếp (8 tests):** Kiểm thử lọc kết hợp (danh mục + thương hiệu + khoảng giá), xử lý sản phẩm chưa có giá (không coi là 0đ, lọc riêng, sắp xếp nulls_last).
7. **So sánh sản phẩm (8 tests):** So sánh hợp lệ 2-3 sản phẩm, từ chối thêm trùng sản phẩm, từ chối vượt quá 3 sản phẩm, từ chối sản phẩm khác danh mục, loại bỏ sản phẩm nháp, hiển thị "Chưa có thông tin" khi thiếu spec, đúng thứ tự định nghĩa danh mục.
8. **Tìm kiếm (8 tests):** Tìm kiếm hoa/thường, tìm kiếm tiếng Việt không dấu (`unaccent`), xử lý chuỗi rỗng/khoảng trắng, tự động rút gọn từ khóa quá dài > 120 ký tự, loại bỏ bài viết nháp/tương lai, phân tách sản phẩm và bài viết.
9. **Giao diện & Điều hướng (3 tests):** Kiểm tra cấu trúc menu 4 mục (`Trang chủ | Bài viết | Phương pháp | Sản phẩm ▾`), kiểm tra active state, responsive layout.

---

## 8. Hướng Dẫn Vận Hành Quản Trị & Biên Tập (Admin Workflow)

### 1. Tạo Tài Khoản Quản Trị Viên Đầu Tiên
```bash
python manage.py createsuperuser
```
Đăng nhập tại: `http://127.0.0.1:8000/admin/`

### 2. Luồng Biên Tập Danh Mục, Sản Phẩm & Xuất Bản
1. **Tạo Danh mục (Category):** Vào *Catalog > Danh mục*, nhập tên danh mục (ví dụ: *Chuột máy tính*), thứ tự hiển thị (`display_order`). Đặt trạng thái `published` để danh mục hiển thị trên menu.
2. **Khai báo Thông số chuẩn (SpecificationDefinition):** Vào *Catalog > Định nghĩa thông số kỹ thuật*, gán các thông số kỹ thuật thuộc danh mục (ví dụ: DPI, Kiểu kết nối, Độ ồn switch, Khối lượng).
3. **Thêm Sản phẩm (Product):**
   - Vào *Catalog > Sản phẩm*, chọn danh mục, điền Tên, Thương hiệu, Model, Mô tả ngắn.
   - Thêm ảnh sản phẩm vào khối inline *Hình ảnh sản phẩm* (hệ thống tự động kiểm tra định dạng JPG/PNG/WEBP và dung lượng <= 5MB).
   - Nhập giá trị cho từng thông số kỹ thuật tương ứng.
   - **Trạng thái:** Mặc định là `Bản nháp (draft)`. Khi hoàn thiện thông số và ảnh, đổi sang `Đã xuất bản (published)`.
4. **Viết và Xuất bản Bài viết (Article):**
   - Vào *Content > Bài viết*, chọn Loại bài (*Đánh giá chi tiết*, *So sánh đối đầu*, *Cẩm nang chọn mua*).
   - Soạn thảo nội dung bằng Markdown. Hệ thống tự động làm sạch (sanitization) chống mã độc XSS.
   - Chọn tác giả, tải ảnh thumbnail đại diện (chỉ nhận JPG/PNG/WEBP <= 5MB).
   - Gắn các sản phẩm được đề cập trong bài viết.
   - Điền thông tin minh bạch biên tập: Đã test thực tế hay chưa, thời gian test, phương pháp đo và công bố affiliate.
   - Chọn trạng thái `Đã xuất bản` và thời điểm xuất bản (`published_at`).

### 3. Cấu Hình Nơi Bán (Merchant) & Liên Kết Affiliate (Offer)
1. **Tạo Nơi bán (Merchant):**
   - Vào *Affiliates > Nơi bán / Đối tác*.
   - Khai báo Tên (ví dụ: *Shopee Vietnam*), Website chính thức (`https://shopee.vn`).
   - Khai báo danh sách hostname được chấp nhận (`allowed_hostnames`): ví dụ `shopee.vn, s.shopee.vn`.
   - Chọn Chế độ liên kết mặc định (`link_mode`): Khuyến nghị để *Liên kết trực tiếp (Direct Link)* để tuân thủ điều khoản sàn.
2. **Tạo Nơi bán & Giá tham khảo cho Sản phẩm (Offer):**
   - Vào *Affiliates > Nơi bán & Giá tham khảo (Offers)*.
   - Chọn Sản phẩm và Nơi bán tương ứng.
   - Nhập `affiliate_url` (bắt buộc giao thức HTTPS và hostname phải khớp với whitelist của nơi bán).
   - Nhập giá tham khảo (`price`), thời điểm kiểm tra giá (`price_checked_at`).
   - Có thể chọn ghi đè chế độ liên kết riêng cho Offer nếu chiến dịch cụ thể yêu cầu.

### 4. Quy Trình Nhập Báo Cáo Đối Soát Hoa Hồng (CSV)
1. Đăng nhập tài khoản quản trị có quyền Staff.
2. Truy cập: `http://127.0.0.1:8000/analytics/reconciliation/import/`.
3. Tải về file mẫu [docs/sample_reconciliation.csv](file:///home/tmthang/Affiliate/docs/sample_reconciliation.csv) hoặc dùng nút "Tải file CSV mẫu" trên giao diện.
4. Điền số liệu đối soát từ dashboard tiếp thị liên kết (Shopee/Lazada/AccessTrade).
5. Tải file lên form. Hệ thống tự động kiểm tra cú pháp từng dòng qua Transaction nguyên tử.
6. Xem kết quả thống kê tại Dashboard: `http://127.0.0.1:8000/analytics/dashboard/`.

---

## 9. Hướng Dẫn Triển Khai Thực Tế (Production Deployment)

### 1. Kiến Trúc Triển Khai Khuyến Nghị
```
[ Khách hàng / Bot Google ]
             │ (HTTPS - Cổng 443)
             ▼
      [ Nginx Reverse Proxy ]
             ├── /static/  ──────> Phục vụ trực tiếp từ /staticfiles/
             ├── /media/   ──────> Phục vụ an toàn từ /media/ (chặn thực thi script)
             │
             │ (HTTP nội bộ qua Cổng 8000 hoặc Unix Socket)
             ▼
     [ Gunicorn WSGI Server ]
             │
             ▼
     [ Django 5.2 (Python 3.14) ]
             │
             ▼
    [ PostgreSQL 16+ Database ]
```

### 2. Danh Sách Biến Môi Trường Production (.env)
Tạo file `.env` trên máy chủ production với các giá trị bí mật thực tế:
```ini
# Bắt buộc đổi sang chuỗi ngẫu nhiên bảo mật cao (> 50 ký tự)
DJANGO_SECRET_KEY=b238a7c9f10e4d2...thay_bang_chuoi_ngau_nhien_dai_hon_50_ky_tu

# Bắt buộc False trên môi trường sản xuất
DJANGO_DEBUG=False

# Domain chính thức của website (phân cách bằng dấu phẩy)
DJANGO_ALLOWED_HOSTS=gocphukien.vn,www.gocphukien.vn

# Cấu hình nguồn gốc tin cậy cho CSRF (HTTPS)
CSRF_TRUSTED_ORIGINS=https://gocphukien.vn,https://www.gocphukien.vn

# Sử dụng cấu hình production
DJANGO_SETTINGS_MODULE=config.settings.production

# Bật chuyển hướng HTTPS và nhận diện reverse proxy tin cậy
SECURE_SSL_REDIRECT=True
USE_REVERSE_PROXY=True

# Thông tin kết nối PostgreSQL Production
DB_ENGINE=django.db.backends.postgresql
DB_NAME=gocphukien_prod
DB_USER=gocphukien_user
DB_PASSWORD=mat_khau_database_rat_manh_va_bao_mat
DB_HOST=127.0.0.1
DB_PORT=5432

# Định dạng vùng & múi giờ
TIME_ZONE=Asia/Ho_Chi_Minh
LANGUAGE_CODE=vi
```

### 3. Quy Trình Triển Khai Từng Bước Trên Máy Chủ Linux (Ubuntu/Debian)

#### Bước 1: Thu thập static files
```bash
python manage.py collectstatic --noinput
```

#### Bước 2: Kiểm tra deployment security check của Django
```bash
python manage.py check --deploy --settings=config.settings.production
```
*Kết quả mong đợi:* `System check identified no issues (0 silenced).`

#### Bước 3: Cấu hình Gunicorn Application Server
Sử dụng file cấu hình [deploy/gunicorn.conf.py](file:///home/tmthang/Affiliate/deploy/gunicorn.conf.py):
```bash
# Kiểm tra khởi chạy thử Gunicorn:
gunicorn -c deploy/gunicorn.conf.py config.wsgi:application
```

#### Bước 4: Thiết lập Systemd Service tự động chạy cùng hệ điều hành
Copy file mẫu [deploy/gocphukien.service](file:///home/tmthang/Affiliate/deploy/gocphukien.service) vào `/etc/systemd/system/`:
```bash
sudo cp deploy/gocphukien.service /etc/systemd/system/gocphukien.service
sudo systemctl daemon-reload
sudo systemctl enable gocphukien
sudo systemctl start gocphukien
sudo systemctl status gocphukien
```

#### Bước 5: Cấu hình Nginx Reverse Proxy & Chứng chỉ SSL
Copy file mẫu [deploy/nginx.conf](file:///home/tmthang/Affiliate/deploy/nginx.conf) vào `/etc/nginx/sites-available/`:
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/gocphukien
sudo ln -s /etc/nginx/sites-available/gocphukien /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Cài đặt chứng chỉ SSL Let's Encrypt miễn phí:
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d gocphukien.vn -d www.gocphukien.vn
```

---

## 10. Chiến Lược Sao Lưu, Khôi Phục, Cập Nhật & Rollback

### 1. Kịch Bản Sao Lưu Định Kỳ (Backup)
Khuyến nghị thiết lập cronjob chạy hàng ngày vào 02:00 sáng:

```bash
# 1. Sao lưu cơ sở dữ liệu PostgreSQL (định dạng nén Custom Format):
pg_dump -U gocphukien_user -h 127.0.0.1 -Fc gocphukien_prod > /backup/db/gocphukien_db_$(date +%Y%m%d_%H%M%S).dump

# 2. Sao lưu toàn bộ tệp hình ảnh media do người dùng tải lên:
tar -czvf /backup/media/gocphukien_media_$(date +%Y%m%d_%H%M%S).tar.gz -C /home/tmthang/Affiliate media/
```

### 2. Quy Trình Khôi Phục Dữ Liệu (Restore)
Khi cần khôi phục lại hệ thống từ bản sao lưu:
```bash
# 1. Tạm dừng service ứng dụng
sudo systemctl stop gocphukien

# 2. Khôi phục cơ sở dữ liệu PostgreSQL (tùy chọn -c để xóa tạo lại bảng sạch sẽ):
pg_restore -U gocphukien_user -h 127.0.0.1 -d gocphukien_prod -c /backup/db/gocphukien_db_YYYYMMDD_HHMMSS.dump

# 3. Khôi phục thư mục media:
tar -xzvf /backup/media/gocphukien_media_YYYYMMDD_HHMMSS.tar.gz -C /home/tmthang/Affiliate/

# 4. Khởi động lại service
sudo systemctl start gocphukien
```

### 3. Quy Trình Cập Nhật Phiên Bản Mới (Deploy Update)
Khi có bản cập nhật mã nguồn mới từ kho Git:
```bash
cd /home/tmthang/Affiliate
source .venv/bin/activate

# 1. Kéo mã nguồn mới nhất
git pull origin main

# 2. Cài đặt các thư viện mới (nếu có)
pip install -r requirements.txt

# 3. Áp dụng migration cơ sở dữ liệu
python manage.py migrate

# 4. Thu thập lại static files
python manage.py collectstatic --noinput

# 5. Khởi động lại Gunicorn không gián đoạn (Graceful Reload)
sudo systemctl reload gocphukien
```

### 4. Quy Trình Khôi Phục Phiên Bản Cũ (Rollback)
Nếu bản cập nhật phát sinh sự cố không mong muốn:
```bash
cd /home/tmthang/Affiliate
source .venv/bin/activate

# 1. Trở về commit ổn định trước đó
git checkout <commit_hash_on_dinh>

# 2. Nếu có migration cần đảo ngược, chạy:
# python manage.py migrate <app_name> <migration_number_truoc_do>
# Hoặc khôi phục lại database từ bản dump trước khi deploy

# 3. Thu thập lại static files
python manage.py collectstatic --noinput

# 4. Khởi động lại service
sudo systemctl restart gocphukien
```



