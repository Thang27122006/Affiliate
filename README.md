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

## 5. Kiểm Thử Hệ Thống (Unit Tests)
Dự án bao gồm 46 bài kiểm thử tự động bao phủ toàn bộ các luồng nghiệp vụ:
```bash
python manage.py test
```

**Các nhóm kiểm thử chính:**
1. **Catalog Constraints & Data Integrity:** Ràng buộc giá Decimal > 0, chống gán spec sai danh mục, chống trùng spec trên cùng 1 sản phẩm, tự động sinh slug duy nhất chống xung đột.
2. **Bộ lọc & Sắp xếp:** Kiểm thử lọc kết hợp (danh mục + thương hiệu + khoảng giá), xử lý sản phẩm chưa có giá (không coi là 0đ, lọc riêng, sắp xếp nulls_last).
3. **So sánh sản phẩm:** So sánh hợp lệ 2-3 sản phẩm, từ chối thêm trùng sản phẩm, từ chối vượt quá 3 sản phẩm, từ chối sản phẩm khác danh mục, loại bỏ sản phẩm nháp, hiển thị "Chưa có thông tin" khi thiếu spec, đúng thứ tự định nghĩa danh mục.
4. **Tìm kiếm:** Tìm kiếm hoa/thường, tìm kiếm tiếng Việt không dấu (`unaccent`), xử lý chuỗi rỗng/khoảng trắng, tự động rút gọn từ khóa quá dài > 120 ký tự, loại bỏ bài viết nháp/tương lai, phân tách sản phẩm và bài viết.
5. **Giao diện & Điều hướng:** Kiểm tra cấu trúc menu 4 mục (`Trang chủ | Bài viết | Phương pháp | Sản phẩm ▾`), kiểm tra active state, responsive layout.
