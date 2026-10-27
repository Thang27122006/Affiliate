# BÁO CÁO TỔNG KẾT DỰ ÁN “GÓC PHỤ KIỆN”
**Chuyên trang đánh giá, so sánh phụ kiện công nghệ học tập & làm việc sinh viên**  
*Mô hình kinh doanh: Tiếp thị liên kết (Affiliate Marketing)*

---

| Thông Tin Chung | Chi Tiết |
| :--- | :--- |
| **Dự án** | Góc Phụ Kiện (Affiliate Web Application) |
| **Phiên bản mã nguồn** | Branch `promt8` (Production-Ready Technical Build) |
| **Framework & Ngôn ngữ** | Python 3.14.4 / Django 5.2.18 |
| **Cơ sở dữ liệu** | PostgreSQL 16+ (kết nối qua `psycopg 3.3.6`) |
| **Giao diện người dùng** | Django Templates, Semantic HTML5, Vanilla CSS, Vanilla JavaScript |
| **Application Server** | Gunicorn 26.2.0 (WSGI) |
| **Web Server / Reverse Proxy**| Nginx (Static & Media Serving, SSL Termination, Gzip) |
| **Múi giờ & Ngôn ngữ** | `Asia/Ho_Chi_Minh` / Tiếng Việt (`vi`) |
| **Kết quả kiểm thử tự động** | **92 / 92 unit tests PASSED (100%)** |
| **Trạng thái kiểm tra bảo mật**| `python manage.py check --deploy` đạt **0 issues (0 silenced)** |

---

## 1. MỤC TIÊU VÀ PHẠM VI DỰ ÁN

### 1.1. Mục tiêu cốt lõi
1. Xây dựng nền tảng nội dung công nghệ độc lập, định hướng phục vụ sinh viên và người đi làm trẻ lựa chọn đúng phụ kiện (chuột máy tính, bàn phím cơ/di động, giá đỡ laptop công thái học) chuẩn ngân sách.
2. Tạo nguồn doanh thu bền vững thông qua tiếp thị liên kết (Affiliate Marketing) mà không làm tăng chi phí của độc giả.
3. Tuyệt đối minh bạch: không bán hàng trực tiếp, không giỏ hàng, không thanh toán, không đăng ký tài khoản độc giả, không chatbot hoặc chức năng AI giả mạo trải nghiệm, không bịa đặt số liệu đo đạc hay đánh giá trải nghiệm giả.

### 1.2. Các phân hệ nghiệp vụ chính (Apps)
Dự án được tổ chức theo kiến trúc module hóa rõ ràng (Decoupled Modular Architecture):
* **`apps.core`**: Quản lý layout, model nền tảng `TimeStampedModel`, công cụ SEO kỹ thuật (`Sitemap`, `robots.txt`, dynamic canonical, Schema.org JSON-LD), bộ làm sạch XSS `render_safe_markdown`, validator an toàn hình ảnh `validate_image_file`, tra cứu tiếng Việt không dấu (`unaccent`).
* **`apps.catalog`**: Quản lý danh mục phụ kiện, thông số kỹ thuật động theo từng danh mục (`SpecificationDefinition`, `ProductSpecification`), thư viện ảnh sản phẩm (`ProductImage`), bộ lọc đa tiêu chí và so sánh đối đầu sản phẩm (2–3 mẫu cùng loại).
* **`apps.content`**: Quản lý bài viết biên tập (`Article`) với 3 mẫu cấu trúc chuẩn (Review chi tiết, So sánh đối đầu, Cẩm nang chọn mua), các trường minh bạch trải nghiệm (thời gian thử nghiệm, phương pháp đo, nguồn gốc sản phẩm, công bố tiếp thị).
* **`apps.affiliates`**: Quản lý đối tác phân phối (`Merchant`), danh sách whitelist hostname, quản lý liên kết nơi bán và giá tham khảo (`Offer`), hỗ trợ 2 chế độ link (Direct Link và Internal Redirect), cơ chế phòng chống Open Redirect và SSRF.
* **`apps.analytics`**: Ghi nhận sự kiện kỹ thuật chịu lỗi cao (`PageView`, `ClickEvent`), bảo vệ quyền riêng tư độc giả, dashboard báo cáo nội bộ dành riêng cho quản trị viên (`Staff Only`), module nhập và đối soát hoa hồng qua file CSV nội bộ (Idempotent, Transaction atomic), management command dọn dẹp dữ liệu cũ.

---

## 2. KẾT QUẢ ĐÁNH GIÁ CHẤT LƯỢNG KỸ THUẬT & KIỂM THỬ

### 2.1. Kết quả kiểm thử tự động (Unit Tests)
Toàn bộ **92 bài kiểm thử tự động** chạy trên cơ sở dữ liệu PostgreSQL độc lập đạt **100% Thành Công (`OK`)** trong thời gian trung bình **16.3 – 16.5 giây**:

| Phân hệ kiểm thử | Số lượng bài test | Nội dung kiểm thử chính | Kết quả |
| :--- | :---: | :--- | :---: |
| **SEO Kỹ Thuật & Sitemaps** | 8 tests | Kiểm tra `robots.txt`, `sitemap.xml` chỉ chứa nội dung đã xuất bản, loại bỏ nháp/tương lai, Canonical URL động theo domain thực tế, thẻ `noindex, follow` trên tìm kiếm/bộ lọc, Structured Data (`BreadcrumbList`, `Article` không có rating giả). | ✅ 100% Passed |
| **Bảo Mật Upload Hình Ảnh** | 5 tests | Chấp nhận JPG/PNG/WEBP; từ chối tuyệt đối SVG (chống Stored XSS); chặn file thực thi (.php, .html, .exe); chặn file text giả mạo đuôi ảnh; giới hạn dung lượng <= 5MB. | ✅ 100% Passed |
| **Analytics & Đối Soát CSV** | 20 tests | Quyền hạn Staff Only; múi giờ `Asia/Ho_Chi_Minh`; tính toán CTR sự kiện chống chia cho 0; ghi nhận PageView/ClickEvent chịu lỗi; import CSV đối soát tính Idempotent (không nhân đôi); transaction atomic rollback khi lỗi; tách bạch tiền tệ; command dọn dẹp dữ liệu cũ. | ✅ 100% Passed |
| **Affiliate Safety & Redirect** | 18 tests | Bắt buộc HTTPS; bảo toàn query params tracking; chặn HTTP/javascript/data/file; chặn URL chứa credentials; whitelist hostname chống giả mạo; 2 chế độ link direct/redirect; 404 khi offer inactive hoặc sản phẩm/danh mục nháp; chống Open Redirect; fault-tolerance khi logging thất bại. | ✅ 100% Passed |
| **Catalog & Data Integrity** | 14 tests | Ràng buộc giá Decimal > 0; chống gán thông số sai danh mục; chống trùng thông số trên 1 sản phẩm; tự động sinh slug duy nhất chống xung đột; chuẩn hóa `get_absolute_url()`. | ✅ 100% Passed |
| **Bộ Lọc Đa Tiêu Chí** | 8 tests | Lọc kết hợp danh mục + thương hiệu + khoảng giá tham khảo; xử lý riêng biệt sản phẩm chưa rõ giá (không coi là 0đ, sắp xếp `nulls_last`). | ✅ 100% Passed |
| **So Sánh Đối Đầu** | 8 tests | So sánh 2–3 sản phẩm cùng danh mục; từ chối thêm trùng; từ chối khác danh mục; loại bỏ sản phẩm nháp; hiển thị "Chưa có thông tin" khi thiếu thông số; sắp xếp đúng thứ tự định nghĩa danh mục. | ✅ 100% Passed |
| **Tìm Kiếm Toàn Trang** | 8 tests | Tìm kiếm không phân biệt hoa thường; tìm kiếm tiếng Việt không dấu (`unaccent`); xử lý chuỗi rỗng/khoảng trắng; tự động rút gọn từ khóa dài > 120 ký tự; loại bỏ bài nháp/tương lai; phân tách sản phẩm và bài viết. | ✅ 100% Passed |
| **Giao Diện & Menu** | 3 tests | Kiểm tra cấu trúc menu 4 mục (`Trang chủ | Bài viết | Phương pháp | Sản phẩm ▾`); dropdown danh mục; active state và responsive. | ✅ 100% Passed |
| **TỔNG CỘNG** | **92 tests** | **Toàn bộ hệ thống vận hành đúng quy chuẩn nghiệp vụ và an toàn.** | **✅ 92/92 OK** |

### 2.2. Tính nhất quán Cơ sở dữ liệu & Migrations
* Lệnh kiểm tra `python manage.py makemigrations --check` trả về: `No changes detected`.
* 100% các file migrations từ `0001_initial` đến nay đều đã được áp dụng đầy đủ và khớp chính xác với models.
* Không có migration dở dang, không có trường dữ liệu thừa.

---

## 3. BÁO CÁO ĐÁNH GIÁ AN TOÀN & BẢO MẬT (SECURITY AUDIT)

```
                            LƯỚI BẢO MẬT HỆ THỐNG
   ┌────────────────────────────────────────────────────────────────────────┐
   │ 1. PHÂN QUYỀN: Staff-only cho Analytics Dashboard & Import CSV        │
   │ 2. CHỐNG XSS: Bleach HTML Sanitizer Whitelist cho Markdown             │
   │ 3. CHỐNG CSRF: Bắt buộc CsrfViewMiddleware + Token cho mọi Form POST   │
   │ 4. CHỐNG OPEN REDIRECT: Chỉ nhận Offer ID; Whitelist Hostname nghiêm ngặt│
   │ 5. UPLOAD MEDIA: Chặn hoàn toàn SVG, chặn file thực thi, giới hạn 5MB   │
   │ 6. QUYỀN RIÊNG TƯ: Cam kết 4 KHÔNG (Không IP thô, không fingerprint...)│
   │ 7. PRODUCTION HEADERS: HSTS 1 năm, SSL Redirect, Secure Cookies        │
   └────────────────────────────────────────────────────────────────────────┘
```

1. **Kiểm soát quyền truy cập:**
   * Giao diện Dashboard thống kê kinh doanh và cổng import CSV được bảo vệ bởi decorator `@staff_member_required(login_url="/admin/login/")`.
   * Khách vãng lai và người dùng thông thường bị chặn tuyệt đối và chuyển hướng đăng nhập.
2. **Chống tấn công chèn mã (XSS):**
   * Bài viết biên tập sử dụng Markdown được làm sạch qua [apps/core/utils.py](file:///home/tmthang/Affiliate/apps/core/utils.py) bằng `bleach`.
   * Whitelist rõ ràng các thẻ văn bản an toàn (`p`, `h1`-`h6`, `strong`, `em`, `table`, `img`, `a`...).
   * Toàn bộ thẻ `<script>`, `<style>`, thuộc tính nguy hại (`onerror`, `onload`, `javascript:`) bị loại bỏ triệt để.
3. **Chống tấn công giả mạo yêu cầu (CSRF):**
   * Tất cả các form gửi dữ liệu lên server (Upload CSV đối soát, đăng nhập quản trị) đều có `{% csrf_token %}`.
   * `CSRF_COOKIE_SECURE = True`, `CSRF_COOKIE_HTTPONLY = True`.
4. **An toàn liên kết nơi bán & Phòng chống Open Redirect / SSRF:**
   * URL affiliate bắt buộc giao thức HTTPS; chặn thông tin đăng nhập trong URL (`user:pass@domain`).
   * Phân tích URL bằng `urllib.parse.urlsplit` và so khớp chính xác với `allowed_hostnames` của nơi bán (chặn domain mạo danh như `shopee.vn.evil.com`).
   * Endpoint `/go/<offer_id>/` chỉ chấp nhận số nguyên ID của Offer đã duyệt, không chấp nhận URL đích tự do từ query param của người dùng.
   * Backend không tải nội dung URL đối tác (không phát sinh nguy cơ SSRF).
5. **An toàn tệp tin tải lên (Media Upload Security):**
   * Sử dụng [apps/core/validators.py](file:///home/tmthang/Affiliate/apps/core/validators.py) kiểm tra cả phần mở rộng (`.jpg`, `.jpeg`, `.png`, `.webp`) và cấu trúc header thực tế qua Pillow.
   * **Chặn tuyệt đối tệp `.svg`** nhằm loại trừ hoàn toàn nguy cơ Stored XSS ẩn trong mã XML của SVG.
   * Chặn file thực thi (`.php`, `.html`, `.exe`) và giới hạn dung lượng tối đa 5MB.
6. **Bảo mật quyền riêng tư độc giả (Privacy by Design):**
   * Cam kết 4 KHÔNG: Không lưu địa chỉ IP thô, Không fingerprinting thiết bị, Không dùng cookie cá nhân theo dõi liên trang, Không thu thập hay can thiệp thông tin cá nhân (PII) của người mua hàng trên các sàn đối tác.
7. **Cấu hình Production Security Check:**
   * Chạy `python manage.py check --deploy --settings=config.settings.production` đạt **0 cảnh báo**.
   * Bật `SECURE_SSL_REDIRECT = True`, `SECURE_HSTS_SECONDS = 31536000` (1 năm), `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`, `SECURE_HSTS_PRELOAD = True`.
   * Chỉ bật `SECURE_PROXY_SSL_HEADER` khi biến môi trường `USE_REVERSE_PROXY=True` được khai báo rõ ràng, loại bỏ nguy cơ giả mạo proxy header.

---

## 4. TỐI ƯU HIỆU NĂNG & TRẢI NGHIỆM NGƯỜI DÙNG (PERFORMANCE & UX)

1. **Tối ưu truy vấn cơ sở dữ liệu (Database Queries):**
   * Loại bỏ triệt để vấn đề truy vấn lặp (N+1 queries).
   * Mọi views danh sách và chi tiết đều sử dụng `select_related` cho các quan hệ 1-1/n-1 (`category`, `author`, `merchant`) và `prefetch_related` cho quan hệ n-n/1-n (`images`, `offers`).
   * Trang chủ tải dữ liệu chỉ trong 3–4 truy vấn SQL đơn lẻ.
2. **Tối ưu tốc độ tải trang & Core Web Vitals:**
   * **Tối ưu LCP (Largest Contentful Paint):** Ảnh chính đầu trang (`product-main-img` tại trang sản phẩm, ảnh thumbnail hero tại trang bài viết) được thiết lập `loading="eager"` và `fetchpriority="high"`.
   * **Tối ưu tải tài nguyên:** Tất cả hình ảnh nằm dưới màn hình đầu (bài viết liên quan, sản phẩm gợi ý, danh sách lưới) sử dụng `loading="lazy"`.
   * **Tối ưu CLS (Cumulative Layout Shift):** Thiết lập tỷ lệ khung hình (`aspect-ratio: 16/9`) và kích thước `width`, `height` rõ ràng.
3. **Phân trang máy chủ (Server-side Pagination):**
   * 12 sản phẩm / trang tại danh mục và danh sách sản phẩm.
   * 9 bài viết / trang tại danh sách bài viết.
4. **Khả năng tiếp cận & Sử dụng (Accessibility - a11y):**
   * Hỗ trợ liên kết ẩn "Chuyển đến nội dung chính" (`skip-link`) cho người dùng bàn phím.
   * `:focus-visible` viền 2px tương phản rõ ràng.
   * Menu dropdown hỗ trợ phím Tab, Enter, Space, Escape.
   * Bảng so sánh được thiết kế khối cuộn ngang `overflow-x: auto; -webkit-overflow-scrolling: touch` kèm cột tiêu đề cố định `position: sticky; left: 0`, đảm bảo thao tác mượt mà trên điện thoại.

---

## 5. BÁO CÁO PHÂN LOẠI TÌNH TRẠNG DỰ ÁN (A - B - C)

### Nhóm A. Đã Hoàn Thành Và Đã Kiểm Chứng Tự Động (Ready & Verified)
* Toàn bộ 92 bài unit test bao phủ các phân hệ nghiệp vụ, bảo mật và SEO.
* Luồng quản trị: Tạo danh mục, sản phẩm, thông số, bài viết, đối tác, offer.
* Cơ chế bảo vệ bản nháp: Ẩn hoàn toàn khỏi trang công khai, URL, tìm kiếm, sitemap.
* Luồng người đọc: Tìm kiếm có dấu/không dấu, lọc đa tiêu chí, xem chi tiết, so sánh đối đầu 2–3 sản phẩm.
* Luồng affiliate an toàn: 2 chế độ link, whitelist hostname, chống Open Redirect/SSRF, bảo toàn tracking params.
* Ghi nhận click/view chịu lỗi cao và bảo vệ quyền riêng tư độc giả.
* Import đối soát CSV hoa hồng định dạng nội bộ có tính Idempotent và rollback giao dịch khi có lỗi.
* Dashboard báo cáo quản trị nội bộ chuẩn múi giờ Việt Nam.
* Bộ lọc XSS Bleach, Validator upload ảnh chặn SVG và file thực thi.
* Cấu hình Production Settings đạt chuẩn bảo mật `check --deploy` (0 issues).
* Tệp cấu hình máy chủ: Gunicorn ([deploy/gunicorn.conf.py](file:///home/tmthang/Affiliate/deploy/gunicorn.conf.py)), Nginx ([deploy/nginx.conf](file:///home/tmthang/Affiliate/deploy/nginx.conf)), Systemd ([deploy/gocphukien.service](file:///home/tmthang/Affiliate/deploy/gocphukien.service)).

### Nhóm B. Đã Triển Khai Nhưng Chưa Kiểm Chứng Mạng Thật (Implemented, Awaiting Live Env)
1. **Kết nối API trực tiếp với các sàn TMĐT (Shopee, Lazada, Tiki...):**
   * *Lý do:* Chưa có tài khoản Publisher chính thức và API credentials; hiện đã kiểm chứng đầy đủ bằng cơ chế link tracking chuẩn và file đối soát CSV nội bộ.
2. **Cấu hình chứng chỉ SSL/TLS Let's Encrypt và Nginx trên server thực tế:**
   * *Lý do:* Dự án đang chạy trên môi trường phát triển cục bộ; file cấu hình Nginx và Systemd đã hoàn thiện sẵn sàng đưa lên server Linux thật.
3. **Đo đạc hiệu năng chịu tải mạng Internet thực tế (Concurrence / Load testing):**
   * *Lý do:* Mới kiểm thử hiệu năng xử lý nội bộ qua Gunicorn sync workers trên máy phát triển; chưa có hạ tầng mạng công cộng để đo độ trễ mạng thực tế.

### Nhóm C. Cần Chủ Website Cung Cấp Hoặc Quyết Định Trước Khi Vận Hành
1. **Tên miền chính thức (Production Domain) & DNS:** Cung cấp tên miền (ví dụ: `gocphukien.vn`) và trỏ bản ghi A/CNAME về địa chỉ IP máy chủ.
2. **Hạ tầng máy chủ (VPS / Cloud Server):** Thuê máy chủ Linux (Ubuntu 22.04 / 24.04 LTS), mở cổng 80 (HTTP) và 443 (HTTPS).
3. **Mã bí mật sản xuất (`DJANGO_SECRET_KEY`):** Sinh chuỗi ngẫu nhiên bảo mật cao (> 50 ký tự) cho file `.env` trên máy chủ thật.
4. **Tài khoản Tiếp thị Liên kết chính thức:** Đăng ký đối tác với Shopee Vietnam, Lazada, Tiki, AccessTrade... để lấy link tracking thật đưa vào hệ thống.
5. **Thông tin liên hệ & Nội dung bài viết thực tế:** Cung cấp email liên hệ biên tập thật; biên tập các bài viết đánh giá thực tế và thông số kỹ thuật kiểm chứng của sinh viên để thay thế dữ liệu demo.

---

## 6. TUYÊN BỐ TRUNG THỰC VỀ TÌNH TRẠNG THỰC TẾ

> 📢 **TUYÊN BỐ QUAN TRỌNG:**  
> Website **"Góc Phụ Kiện"** hiện tại **đã hoàn tất 100% về mặt nền tảng kỹ thuật, cấu trúc cơ sở dữ liệu, các luồng nghiệp vụ, kiểm thử tự động và bảo mật hệ thống**.  
> **TUY NHIÊN, WEBSITE CHƯA ĐỦ ĐIỀU KIỆN KINH DOANH THỰC TẾ** do chưa có tên miền chính thức, chưa có liên kết affiliate thật từ các sàn thương mại điện tử đối tác và chưa có nội dung đánh giá thực tế từ ban biên tập. Dự án tuân thủ nghiêm ngặt nguyên tắc trung thực: **không tự ý tạo dữ liệu doanh số hoặc đánh giá trải nghiệm giả để tuyên bố sẵn sàng kinh doanh**.

---

*Báo cáo được lập tự động từ kết quả kiểm thử thực tế và mã nguồn dự án "Góc Phụ Kiện".*
