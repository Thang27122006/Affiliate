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

## 6. Kiểm Thử Hệ Thống (Unit Tests)
Dự án bao gồm **65 bài kiểm thử tự động** bao phủ toàn bộ các luồng nghiệp vụ:
```bash
python manage.py test
```

**Các nhóm kiểm thử chính:**
1. **Affiliate Link Safety & Redirect (18 tests):** Bắt buộc HTTPS, giữ nguyên tham số tracking, chặn HTTP/javascript/data/file, chặn URL chứa credentials, chặn hostname giả mạo mạo danh subdomain, kiểm tra 2 chế độ direct/redirect và override, redirect 302 thành công, 404 khi offer/merchant inactive hoặc product/category draft, chống Open Redirect, tính chịu lỗi khi logging thất bại.
2. **Analytics Click Tracking & Privacy (6 tests):** Ghi nhận direct click thành công, xác minh model không lưu IP thô/fingerprint/PII, debounce throttle 3 giây chống spam lặp, từ chối input lỗi/inactive, xác minh thẻ HTML có href thật hoạt động ngay cả khi JS tắt hoặc tracking lỗi.
3. **Catalog Constraints & Data Integrity:** Ràng buộc giá Decimal > 0, chống gán spec sai danh mục, chống trùng spec trên cùng 1 sản phẩm, tự động sinh slug duy nhất chống xung đột.
4. **Bộ lọc & Sắp xếp:** Kiểm thử lọc kết hợp (danh mục + thương hiệu + khoảng giá), xử lý sản phẩm chưa có giá (không coi là 0đ, lọc riêng, sắp xếp nulls_last).
5. **So sánh sản phẩm:** So sánh hợp lệ 2-3 sản phẩm, từ chối thêm trùng sản phẩm, từ chối vượt quá 3 sản phẩm, từ chối sản phẩm khác danh mục, loại bỏ sản phẩm nháp, hiển thị "Chưa có thông tin" khi thiếu spec, đúng thứ tự định nghĩa danh mục.
6. **Tìm kiếm:** Tìm kiếm hoa/thường, tìm kiếm tiếng Việt không dấu (`unaccent`), xử lý chuỗi rỗng/khoảng trắng, tự động rút gọn từ khóa quá dài > 120 ký tự, loại bỏ bài viết nháp/tương lai, phân tách sản phẩm và bài viết.
7. **Giao diện & Điều hướng:** Kiểm tra cấu trúc menu 4 mục (`Trang chủ | Bài viết | Phương pháp | Sản phẩm ▾`), kiểm tra active state, responsive layout.

