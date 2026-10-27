"""
Cấu hình Gunicorn WSGI Application Server cho 'Góc Phụ Kiện' (Production).
Chạy: gunicorn -c deploy/gunicorn.conf.py config.wsgi:application
"""
import multiprocessing
import os

# Địa chỉ và cổng lắng nghe (có thể dùng Unix Socket hoặc TCP Port)
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")

# Số lượng worker processes: Công thức khuyến nghị (2 * số cores) + 1
workers = int(os.environ.get("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))

# Kiểu worker đồng bộ chuẩn mực cho Django
worker_class = "sync"

# Giới hạn thời gian xử lý một request (tránh treo worker)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 30))
keepalive = 2

# Tái khởi động worker sau một số lượng request để ngăn rò rỉ bộ nhớ (memory leak)
max_requests = 1000
max_requests_jitter = 50

# Nhật ký (Logging)
loglevel = "info"
accesslog = "-"  # Ghi ra stdout (dễ dàng quản lý qua systemd/docker)
errorlog = "-"   # Ghi ra stderr

# Tên tiến trình
proc_name = "gocphukien_gunicorn"

# Người dùng và nhóm chạy tiến trình (tùy chỉnh khi chạy trên server)
# user = "www-data"
# group = "www-data"
