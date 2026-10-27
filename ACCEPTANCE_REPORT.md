# BIÊN BẢN NGHIỆM THU DỰ ÁN “GÓC PHỤ KIỆN”
**Dựa trên mã nguồn, cấu hình và kết quả thực thi kiểm thử thực tế trên hệ thống**  
*Môi trường: Linux x86_64 | Python 3.14.4 | Django 5.2.18 | PostgreSQL 18.6*

---

## 1. XÁC ĐỊNH HIỆN TRẠNG DỰ ÁN

| Hạng mục rà soát | Tình trạng hiện tại | Chi tiết kỹ thuật & Đánh giá |
| :--- | :---: | :--- |
| **Kiến trúc công nghệ** | Chuẩn xác | Giữ nguyên 100% stack `Python 3.14` + `Django 5.2.18` + `PostgreSQL 18.6` (kết nối qua `psycopg 3.3.6`). Không sử dụng thư viện lạ ngoài phạm vi. |
| **Cấu trúc module (Apps)** | Hoàn thiện | 5 ứng dụng độc lập, phân tách trách nhiệm rõ ràng: `apps.core`, `apps.catalog`, `apps.content`, `apps.affiliates`, `apps.analytics`. |
| **Giao diện & Styling** | Hoàn thiện | Django Templates + HTML5 ngữ nghĩa + Vanilla CSS + Vanilla JavaScript. Không dùng TailwindCSS hay React/Vue framework nặng nề. |
| **Cấu trúc Menu** | Đúng yêu cầu | Menu chính hiển thị đúng thứ tự: **Trang chủ | Bài viết | Phương pháp | Sản phẩm ▾**. Trong đó, Chuột, Bàn phím, Giá đỡ laptop đã được gom vào dropdown của **Sản phẩm** cùng với nút "Tất cả sản phẩm". |
| **Dữ liệu thực tế trong DB** | Dữ liệu mẫu ban đầu | Có sẵn 3 danh mục đã xuất bản, 8 sản phẩm, 2 đối tác sàn (Shopee, Lazada), 8 offer affiliate và 1 bài viết mẫu chuẩn biên tập. Chưa có bài viết và đánh giá thực tế trên quy mô lớn. |

---

## 2. KẾT QUẢ KIỂM TRA KỸ THUẬT

### 2.1. Django System Check & Migrations
- **Lệnh thực thi:** `python manage.py check`  
  **Kết quả:** `System check identified no issues (0 silenced)`. Đạt 100%.
- **Kiểm tra Migrations mới:** `python manage.py makemigrations --check --dry-run`  
  **Kết quả:** `No changes detected`. Đạt 100% (Model và schema đồng bộ hoàn toàn).
- **Kiểm tra Migration chưa áp dụng:** `python manage.py showmigrations | grep '\[ \]'`  
  **Kết quả:** Trả về rỗng. 100% migrations từ `0001_initial` đến nay đều đã áp dụng `[X]` trên PostgreSQL.

### 2.2. Xác minh Cơ sở dữ liệu PostgreSQL
- **Database Engine:** `django.db.backends.postgresql`
- **Tên cơ sở dữ liệu:** `gocphukien`
- **Phiên bản Server:** `PostgreSQL 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1) on x86_64-pc-linux-gnu`
- **Port kết nối:** `5432` (cục bộ)
- **Tài khoản kết nối:** `postgres`

### 2.3. Kiểm tra biến môi trường & Bảo mật thông tin
- File cấu hình môi trường `.env` được bảo vệ nghiêm ngặt: nằm trong `.gitignore`.
- Kiểm tra Git index: `git ls-files .env` trả về rỗng (tuyệt đối không bị commit vào Git).
- Tách biệt rõ ràng 2 môi trường: `config/settings/development.py` và `config/settings/production.py`.
- Lệnh `python manage.py check --deploy --settings=config.settings.production` đạt **0 issues (0 silenced)** khi có đủ biến môi trường production.

### 2.4. Kết quả chạy Unit Tests
- **Tổng số bài kiểm thử:** **92 / 92 bài test PASSED (100%)**
- **Thời gian thực thi:** 15.43 giây trên cơ sở dữ liệu test PostgreSQL độc lập (`test_gocphukien`).
- **Phạm vi bao phủ:** Phân quyền, CSRF, XSS filter, Upload ảnh an toàn, SEO sitemap/robots, Link affiliate, Tracking event, CSV Idempotency, Bộ lọc và So sánh sản phẩm.

---

## 3. KẾT QUẢ KIỂM TRA LUỒNG NGƯỜI ĐỌC (READER FLOW)

| Tiêu chí luồng người đọc | Kết quả thực tế | Chi tiết kiểm chứng |
| :--- | :---: | :--- |
| **Trang chủ & Menu điều hướng** | **ĐẠT** | Trang chủ HTTP 200. Menu hiển thị đúng cấu trúc `Trang chủ | Bài viết | Phương pháp | Sản phẩm ▾`. |
| **Dropdown Sản phẩm** | **ĐẠT** | Mở ra các mục: "Tất cả sản phẩm" (`/san-pham/`), "Bàn phím" (`/danh-muc/ban-phim/`), "Chuột máy tính" (`/danh-muc/chuot-may-tinh/`), "Giá đỡ laptop" (`/danh-muc/gia-do-laptop/`). Lấy tự động từ model `Category` đang active. |
| **Cô lập dữ liệu danh mục** | **ĐẠT** | Truy cập `/danh-muc/ban-phim/` chỉ hiển thị các sản phẩm thuộc danh mục Bàn phím; sản phẩm Chuột máy tính tuyệt đối không hiển thị. |
| **Lọc, Tìm kiếm, Sắp xếp & Phân trang** | **ĐẠT** | Kết hợp đồng thời bộ lọc `brand=Logitech&sort=price_asc` trả về HTTP 200 chính xác. Tìm kiếm `/tim-kiem/?q=logitech` chia tách 2 khối rõ ràng: Sản phẩm và Bài viết. Hỗ trợ tìm kiếm tiếng Việt không dấu (`unaccent`). |
| **Chi tiết sản phẩm, bài viết, nơi bán** | **ĐẠT** | Chi tiết sản phẩm hiển thị đầy đủ thông số kỹ thuật dạng bảng, danh sách nơi bán kèm giá tham khảo và khuyến cáo minh bạch về giá. |
| **So sánh sản phẩm** | **ĐẠT** | So sánh 2–3 sản phẩm cùng danh mục hiển thị bảng thông số trực quan; so sánh 2 sản phẩm khác danh mục hiển thị cảnh báo `category_mismatch` thân thiện; sản phẩm trùng lặp được loại trừ sạch sẽ. Bảng so sánh có `overflow-x: auto` và `position: sticky` cho cột đầu. |
| **Bảo vệ nội dung nháp** | **ĐẠT** | Sản phẩm nháp (`draft`), bài viết nháp (`draft`), danh mục không kích hoạt (`inactive`) đều trả về **HTTP 404** khi truy cập trực tiếp và bị loại bỏ 100% khỏi tìm kiếm, danh mục, sitemap. |
| **Trạng thái kiểm chứng giao diện** | **ĐÃ KIỂM CHỨNG BACKEND/MARKUP** | Đã kiểm chứng HTML markup, cấu trúc thẻ ngữ nghĩa, liên kết và logic xử lý thông qua Django Client & cURL. *Lưu ý:* Chưa kiểm chứng trực quan bằng browser subagent (Playwright) do môi trường sandbox thiếu browser binary (lỗi tải driver từ CDN ngoại vi). |

---

## 4. KẾT QUẢ KIỂM TRA LUỒNG QUẢN TRỊ (ADMIN & PERMISSION FLOW)

*Kiểm thử được thực hiện an toàn trong rollback transaction, không làm thay đổi hoặc bẩn cơ sở dữ liệu thật:*

1. **Phân quyền người dùng chưa đăng nhập:**
   - Truy cập `/admin/` -> Chuyển hướng HTTP 302 về `/admin/login/`.
   - Truy cập `/analytics/dashboard/` -> Chuyển hướng HTTP 302 về `/admin/login/`.
   - Truy cập `/analytics/reconciliation/import/` -> Chuyển hướng HTTP 302 về `/admin/login/`.
2. **Phân quyền người dùng thông thường (`is_staff=False`):**
   - Đăng nhập tài khoản độc giả thường, truy cập `/analytics/dashboard/` -> Bị từ chối (HTTP 302 chuyển về trang đăng nhập admin theo chuẩn `UserPassesTestMixin`).
3. **Phân quyền quản trị viên (`is_staff=True`):**
   - Truy cập `/analytics/dashboard/` -> HTTP 200 OK.
   - Truy cập `/analytics/reconciliation/import/` -> HTTP 200 OK.
4. **Vòng đời dữ liệu quản trị (Lifecycle):**
   - Tạo mới Category, Product, Specification, Merchant, Offer, Article ở trạng thái `draft`: Khách công khai truy cập trả về HTTP 404.
   - Chuyển trạng thái sang `published`: Khách công khai truy cập nhận HTTP 200 và thấy nội dung ngay lập tức.
   - Chuyển ngược lại `draft`: Khách công khai truy cập lập tức nhận lại HTTP 404.

---

## 5. KẾT QUẢ KIỂM TRA TIẾP THỊ LIÊN KẾT (AFFILIATE) & THỐNG KÊ

1. **An toàn liên kết và Whitelist Hostname:**
   - Offer chỉ chấp nhận URL HTTPS thuộc hostname đã được duyệt trong `Merchant.allowed_hostnames` (ví dụ: `shopee.vn`, `s.shopee.vn`, `lazada.vn`, `tiki.vn`).
   - Parse hostname chặt chẽ bằng `urllib.parse`, ngăn chặn tấn công chuỗi con, chặn schemes nguy hiểm (`javascript:`, `data:`, `file:`) và URL chứa credentials (`user:pass@host`).
2. **Hai chế độ liên kết:**
   - **Direct Link:** Trỏ trực tiếp đến URL đối tác, kèm thuộc tính `rel="noopener noreferrer sponsored"`.
   - **Internal Redirect (`/go/<offer_id>/`):** Chuyển hướng HTTP 302 an toàn, bảo toàn đầy đủ các tham số tracking (`utm_source`, `aff_sub`).
3. **Chống Open Redirect:**
   - Khi Offer bị vô hiệu hóa (`is_active=False`) hoặc sản phẩm/danh mục chưa xuất bản -> endpoint `/go/<id>/` trả về HTTP 404, tuyệt đối không chuyển hướng.
4. **Ghi nhận sự kiện chịu lỗi cao (Fault-tolerant Tracking):**
   - Lượt bấm affiliate được ghi nhận vào `ClickEvent` trong transaction độc lập. Nếu ghi nhận logging gặp trục trặc, hệ thống vẫn ưu tiên chuyển hướng người dùng an toàn đến nơi bán, không làm gián đoạn trải nghiệm độc giả.
5. **Đối soát hoa hồng qua file CSV nội bộ (Reconciliation):**
   - Định dạng chuẩn 8 cột: `program,transaction_id,item_id,transaction_time,status,commission,currency,tracking_code`.
   - **Tính Idempotent (Chống nhân đôi dữ liệu):** Nhập lặp lại cùng một file CSV nhiều lần không tạo thêm bản ghi mới (`created_count = 0`, `updated_count = N`), tổng số lượng và doanh thu trong database giữ nguyên chính xác.
   - Giao dịch chỉ được gán cho sản phẩm/bài viết khi có `tracking_code` rõ ràng; tuyệt đối không phỏng đoán theo thời gian.
   - Không bịa đặt doanh thu giả hoặc đánh giá sao giả.

---

## 6. CÁC LỖI ĐÃ PHÁT HIỆN VÀ TỰ ĐỘNG KHẮC PHỤC

1. **Ràng buộc toàn vẹn dữ liệu Bài viết (`author_id NOT NULL`):**
   - *Hiện tượng:* Khi tạo bài viết nháp kiểm thử, thiếu trường `author` dẫn đến `IntegrityError` từ PostgreSQL.
   - *Xác nhận:* Đây là ràng buộc toàn vẹn chuẩn xác của mô hình bài viết (mọi bài viết phải gắn với một tác giả biên tập hợp lệ). Script kiểm thử đã được cập nhật cung cấp đầy đủ thông tin tác giả.
2. **Xử lý Context ngoài TestCase runner:**
   - *Hiện tượng:* Khi chạy script kiểm tra độc lập qua `Client()` ngoài test runner của Django, `response.context` không tự động gán nếu view render trực tiếp.
   - *Khắc phục:* Đã chuẩn hóa việc kiểm tra trực tiếp qua cả HTTP Status Code và nội dung HTML phản hồi (`response.content`), đảm bảo đánh giá chính xác những gì người dùng thực tế nhìn thấy.

---

## 7. BẢNG TỔNG HỢP NGHIỆM THU CHI TIẾT

| Chức năng | Đã triển khai | Đã kiểm chứng | Lỗi / Giới hạn phát hiện | Bằng chứng kiểm tra thực tế |
| :--- | :---: | :---: | :--- | :--- |
| **Cấu hình Django & PostgreSQL** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | `check` 0 issues; DB: PostgreSQL 18.6 `gocphukien`. |
| **Hệ thống Migration** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | `makemigrations --check` no changes; 100% applied. |
| **Menu điều hướng 4 mục** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | HTML: `Trang chủ \| Bài viết \| Phương pháp \| Sản phẩm ▾`. |
| **Dropdown danh mục sản phẩm** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Dropdown chứa Tất cả sản phẩm, Bàn phím, Chuột máy tính, Giá đỡ laptop. |
| **Cô lập dữ liệu danh mục** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | `/danh-muc/ban-phim/` chỉ chứa bàn phím, không lọt chuột. |
| **Bộ lọc đa tiêu chí** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Lọc `brand` + `sort` + khoảng giá hoạt động chính xác. |
| **Tìm kiếm có dấu / không dấu** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Tìm kiếm `unaccent` PostgreSQL, phân tách Sản phẩm & Bài viết. |
| **Chi tiết sản phẩm & nơi bán** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Bảng thông số, khối nơi bán, disclaimer giá tham khảo. |
| **So sánh sản phẩm cùng/khác loại**| ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | So sánh cùng loại hiển thị bảng specs; khác loại cảnh báo mismatch; chống trùng. |
| **Bảo vệ nội dung nháp** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Sản phẩm/bài viết nháp trả về 404, không lọt vào tìm kiếm/sitemap. |
| **Phân quyền Quản trị & Analytics**| ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Khách/độc giả thường bị 302 login; Staff truy cập HTTP 200. |
| **Vòng đời nội dung (Lifecycle)** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Draft (404) -> Published (200) -> Unpublish (404) tức thì. |
| **Affiliate Redirect & Whitelist** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Chặn scheme nguy hiểm, 302 đúng đích, bảo toàn tracking params. |
| **Chống Open Redirect** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Offer inactive trả về 404 khi truy cập `/go/<id>/`. |
| **Tracking Event an toàn** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Ghi nhận ClickEvent không làm cản trở redirect; không lưu IP thô. |
| **Đối soát CSV Idempotency** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Import lặp lại cùng 1 file CSV không tạo bản ghi trùng lặp. |
| **SEO Kỹ thuật & Sitemap** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | `robots.txt` chặn `/admin/`, `/go/`; `sitemap.xml` hợp lệ. |
| **Bảo mật Upload Hình ảnh** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | Chỉ nhận JPG/PNG/WEBP <= 5MB; từ chối SVG, PHP, HTML. |
| **Tự động hóa kiểm thử (Tests)** | ĐÃ ĐỦ | ĐÃ ĐẠT | Không có | **92 / 92 unit tests PASSED (100%)**. |
| **Kiểm chứng giao diện trực quan** | ĐÃ ĐỦ | *CHƯA ĐẦY ĐỦ* | Sandbox thiếu browser binary | Đã xác thực HTML/CSS/DOM; chưa chạy được Playwright browser do thiếu driver trên sandbox. |

---

## 8. KẾT LUẬN NGHIỆM THU THEO 3 MỨC

### Mức 1: Khả năng chạy cục bộ (Local Environment)
👉 **KẾT LUẬN: ĐẠT 100% (HOÀN TOÀN SẴN SÀNG)**  
Hệ thống chạy mượt mà trên môi trường cục bộ với Python 3.14, Django 5.2.18 và PostgreSQL 18.6. Mọi tính năng từ giao diện người đọc, bộ lọc, tìm kiếm, so sánh sản phẩm đến quản trị admin, ghi nhận thống kê và đối soát CSV đều hoạt động trơn tru, không có bất kỳ lỗi cú pháp, lỗi logic hay xung đột cơ sở dữ liệu nào.

### Mức 2: Khả năng triển khai thực tế về mặt kỹ thuật (Technical Production Deployment)
👉 **KẾT LUẬN: ĐẠT 100% VỀ MẶT KỸ THUẬT (SẴN SÀNG DEPLOY)**  
Về mặt hạ tầng phần mềm và bảo mật, dự án đã được trang bị đầy đủ:
- Bộ cấu hình sản xuất `config/settings/production.py` đạt **0 issues** khi chạy `check --deploy`.
- File cấu hình WSGI application server chuẩn hiệu năng cao: [deploy/gunicorn.conf.py](file:///home/tmthang/Affiliate/deploy/gunicorn.conf.py).
- File cấu hình Web Server & Reverse Proxy chuẩn bảo mật: [deploy/nginx.conf](file:///home/tmthang/Affiliate/deploy/nginx.conf) (giới hạn upload, chặn truy cập file ẩn, phục vụ static/media tối ưu, security headers).
- File cấu hình tự động quản lý tiến trình: [deploy/gocphukien.service](file:///home/tmthang/Affiliate/deploy/gocphukien.service).
- Cơ chế bảo vệ CSRF, XSS (Bleach), SQL Injection (Django ORM có tham số) và chống Open Redirect.

### Mức 3: Đủ điều kiện kinh doanh và vận hành thương mại thực tế
👉 **KẾT LUẬN: CHƯA ĐẠT (CẦN BỔ SUNG DỮ LIỆU & TÀI NGUYÊN THẬT)**  
Website hiện chưa thể vận hành kinh doanh thực tế vì các lý do sau:
- Chưa có tên miền thật và máy chủ công khai (hiện đang cấu hình cho localhost/127.0.0.1).
- Các liên kết affiliate hiện có chỉ là liên kết mẫu thử nghiệm an toàn, chưa được gắn mã tiếp thị từ tài khoản Publisher chính thức của chủ sở hữu trên các sàn TMĐT.
- Số lượng bài viết review và sản phẩm hiện tại chủ yếu là dữ liệu ban đầu phục vụ kiểm thử kỹ thuật, chưa đủ chiều sâu và khối lượng nội dung thực tế để thu hút độc giả tự nhiên (SEO organic).

---

## 9. DANH MỤC THÔNG TIN & TÀI NGUYÊN BẠN CẦN CUNG CẤP

Để đưa website từ trạng thái "Sẵn sàng kỹ thuật" sang "Vận hành kinh doanh thực tế", bạn cần chuẩn bị và cung cấp các hạng mục sau:

1. **Tên miền chính thức (Domain):**
   - Đăng ký tên miền (ví dụ: `gocphukien.vn` hoặc `gocphukien.com`).
   - Cấu hình bản ghi DNS (A record trỏ về IP máy chủ VPS).
2. **Hạ tầng máy chủ (Hosting / VPS Linux):**
   - Một máy chủ ảo VPS Linux (khuyến nghị: Ubuntu 22.04 LTS hoặc 24.04 LTS, tối thiểu 1 vCPU, 2GB RAM, 25GB SSD).
   - Địa chỉ IP tĩnh và quyền truy cập SSH (root/sudo) để cài đặt Nginx, PostgreSQL và Gunicorn theo các file đã chuẩn bị trong thư mục `deploy/`.
3. **Hình ảnh sản phẩm bản quyền:**
   - Cung cấp hình ảnh chụp thực tế hoặc ảnh được cấp phép sử dụng từ hãng/nhà phân phối (định dạng JPG, PNG hoặc WebP; kích thước chuẩn 800x800 hoặc 1200x800; dung lượng dưới 5MB).
4. **Nội dung đánh giá & đo đạc thực tế:**
   - Các bài viết review thực tế từ quá trình trải nghiệm và đo kiểm phụ kiện dành cho sinh viên.
   - Bảng thông số đo đạc thực tế (trọng lượng cân thật, độ ồn gõ phím dB thật, thời lượng pin thực tế) để điền vào phần thông số kỹ thuật.
5. **Tài khoản Đối tác & Liên kết Affiliate thật:**
   - Đăng ký tài khoản Publisher chính thức trên các sàn thương mại điện tử (Shopee Affiliate Program, Lazada Affiliate, Tiki) hoặc mạng tiếp thị liên kết (AccessTrade, MasOffer).
   - Lấy các đường link tracking hợp lệ chứa mã định danh tiếp thị của bạn để cập nhật vào bảng `Offer` trong trang Quản trị.
6. **Mã khóa bảo mật Production:**
   - Một chuỗi bí mật `DJANGO_SECRET_KEY` ngẫu nhiên dài từ 50 ký tự trở lên để đặt vào file `.env` trên máy chủ thật (không dùng secret key của môi trường phát triển).

---
*Biên bản nghiệm thu được lập ngày 27/10/2026 bởi Antigravity Pair Programmer.*
