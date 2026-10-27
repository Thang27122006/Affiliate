# QUY ƯỚC DỰ ÁN "GÓC PHỤ KIỆN"

Tài liệu này quy định các tiêu chuẩn kiến trúc, quy tắc phát triển và kỷ luật kỹ thuật bắt buộc cho toàn bộ các giai đoạn triển khai của dự án **Góc Phụ Kiện**.

---

## 1. Định Vị & Phạm Vi Sản Phẩm
- **Mục tiêu cốt lõi:** Website đánh giá, so sánh phụ kiện công nghệ học tập và làm việc dành cho sinh viên (chuột, bàn phím, giá đỡ laptop), tạo nguồn thu thông qua tiếp thị liên kết (Affiliate Marketing).
- **Nguyên tắc nghiệp vụ:**
  - Website **không** bán hàng trực tiếp.
  - **Không** xây dựng giỏ hàng, cổng thanh toán, đăng ký tài khoản người đọc (chỉ có tài khoản quản trị).
  - **Không** tích hợp chatbot hoặc AI vào giao diện frontend khi chưa có yêu cầu.
  - **Không** tạo đánh giá trải nghiệm giả, đơn hàng giả hoặc số liệu doanh thu ảo.

---

## 2. Công Nghệ Bắt Buộc (Tech Stack)
- **Ngôn ngữ:** Python (phiên bản đang sử dụng: `Python 3.14.4`).
- **Framework:** Django (phiên bản đang sử dụng: `Django 5.2.18`).
- **Cơ sở dữ liệu:** PostgreSQL (kết nối qua `psycopg 3.x`). Bắt buộc dùng PostgreSQL, không được âm thầm chuyển sang SQLite.
- **Frontend:** Django Templates, Semantic HTML5, Vanilla CSS hiện đại, Vanilla JavaScript thuần. **Không dùng Tailwind CSS, React, Next.js, Flask hoặc FastAPI.**
- **Quản trị nội dung:** Django Admin chuẩn hóa với giao diện tiếng Việt.
- **Kiến trúc:** Django Monolith, chưa tách API và frontend.

---

## 3. Cấu Trúc Module & Trách Nhiệm (Clean Architecture)
Dự án được phân chia thành các app độc lập theo đúng miền nghiệp vụ:
- `apps.core`: Hệ thống cốt lõi, base templates, models cơ sở (`TimeStampedModel`), health check.
- `apps.catalog`: Danh mục sản phẩm (chuột, bàn phím, giá đỡ laptop), thuộc tính, thương hiệu, thông số kỹ thuật.
- `apps.content`: Bài viết đánh giá chuyên sâu, cẩm nang tư vấn chọn mua, so sánh tiêu chí.
- `apps.affiliates`: Quản lý đối tác affiliate, redirect link, theo dõi tham số chiến dịch.
- `apps.analytics`: Ghi nhận sự kiện click tiếp thị liên kết, thống kê lượt truy cập bài viết.

---

## 4. Kỷ Luật & Nguyên Tắc Triển Khai
1. **Triển khai tuần tự theo từng giai đoạn:**
   - Hoàn thành dứt điểm mục tiêu của giai đoạn hiện tại.
   - Không tự ý xây dựng tính năng của các giai đoạn tương lai.
2. **Bảo toàn chức năng đã ổn định:**
   - Không sửa đổi mã nguồn hoặc cấu trúc đã hoạt động tốt nếu không phục vụ trực tiếp cho yêu cầu hiện tại.
3. **Trung thực về lỗi và dữ liệu:**
   - Không che giấu lỗi bằng dữ liệu giả lập (mock data) hoặc cơ chế fallback ngầm.
   - Báo cáo chính xác nguyên nhân khi gặp sự cố môi trường.
4. **Kiểm thử thực tế:**
   - Chỉ xác nhận hoàn thành khi đã thực sự chạy lệnh kiểm tra (`check`, `test`, `migrate`, chạy server) trên môi trường thực tế và có kết quả log thành công.
5. **Bảo mật & Biến môi trường:**
   - Không bao giờ commit file `.env`, mật khẩu, secret key, chứng chỉ, hoặc database dump vào Git.
   - Mọi cấu hình nhạy cảm đều phải nạp từ biến môi trường thông qua `.env`. Luôn duy trì file `.env.example` với dữ liệu mẫu an toàn.
