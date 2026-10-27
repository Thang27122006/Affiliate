from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse


def home_view(request):
    """
    Trang chủ tối giản của dự án 'Góc Phụ Kiện'.
    Xác nhận hệ thống khởi động thành công và hiển thị các thông tin nền tảng.
    """
    db_connected = False
    db_error = None
    try:
        connection.ensure_connection()
        db_connected = True
    except Exception as exc:
        db_error = str(exc)

    context = {
        "title": "Góc Phụ Kiện - Đánh giá & So sánh phụ kiện học tập, làm việc",
        "db_connected": db_connected,
        "db_error": db_error,
        "categories": [
            {
                "id": "chuot",
                "name": "Chuột máy tính",
                "icon": "🖱️",
                "description": "Chuột công thái học, chuột văn phòng êm ái, chuột gaming phục vụ học tập và làm việc.",
            },
            {
                "id": "ban-phim",
                "name": "Bàn phím",
                "icon": "⌨️",
                "description": "Bàn phím cơ, bàn phím silent văn phòng tối ưu gõ phím và bảo vệ cổ tay.",
            },
            {
                "id": "gia-do-laptop",
                "name": "Giá đỡ laptop",
                "icon": "💻",
                "description": "Giá đỡ nâng hạ, nhôm nguyên khối, tản nhiệt giúp tư thế ngồi học chuẩn và giảm mỏi cổ.",
            },
        ],
    }
    return render(request, "core/home.html", context)


def health_check_view(request):
    """
    Endpoint kiểm tra sức khỏe hệ thống (Health Check) và kết nối DB.
    """
    status = "healthy"
    db_status = "connected"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
    except Exception as exc:
        status = "unhealthy"
        db_status = f"error: {exc}"

    return JsonResponse(
        {
            "status": status,
            "database": db_status,
            "project": "Góc Phụ Kiện",
        },
        status=200 if status == "healthy" else 500,
    )
