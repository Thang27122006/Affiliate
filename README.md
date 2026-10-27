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
psql -U postgres -c "CREATE DATABASE gocphukien;"
```

#### Cách 2: Sử dụng Docker Compose (Tuỳ chọn)
```bash
# Khởi chạy container PostgreSQL
docker-compose up -d
```

### Bước 4: Chạy Migration và Tạo Superuser
```bash
# Thực hiện migrate cơ sở dữ liệu
python manage.py migrate

# Tạo tài khoản quản trị viên truy cập Django Admin
python manage.py createsuperuser
```

### Bước 5: Kiểm tra Hệ thống & Khởi chạy Server
```bash
# Chạy system check của Django
python manage.py check

# Khởi chạy máy chủ phát triển
python manage.py runserver
```

Truy cập:
- **Trang chủ:** `http://127.0.0.1:8000/`
- **Quản trị Django Admin:** `http://127.0.0.1:8000/admin/`
- **Kiểm tra trạng thái (Health Check):** `http://127.0.0.1:8000/health/`

---

## 4. Kiểm Thử Hệ Thống
Để kiểm tra tính toàn vẹn của mã nguồn:
```bash
python manage.py test
```
