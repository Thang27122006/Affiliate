/**
 * Góc Phụ Kiện - Client-side interactions
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const menuToggle = document.getElementById('menu-toggle');
    const mainNav = document.getElementById('main-nav');

    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            const isOpen = mainNav.classList.toggle('is-open');
            menuToggle.setAttribute('aria-expanded', String(isOpen));
        });

        // Close mobile nav when clicking outside
        document.addEventListener('click', (e) => {
            if (!mainNav.contains(e.target) && !menuToggle.contains(e.target)) {
                mainNav.classList.remove('is-open');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // 2. Products Dropdown (Desktop click & Mobile accordion, WAI-ARIA support)
    const dropdownWrapper = document.getElementById('nav-dropdown-products');
    const dropdownBtn = document.getElementById('products-dropdown-btn');
    const dropdownMenu = document.getElementById('products-dropdown-menu');

    if (dropdownWrapper && dropdownBtn && dropdownMenu) {
        // Toggle dropdown on button click
        dropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = dropdownBtn.getAttribute('aria-expanded') === 'true';
            const nextState = !isExpanded;
            
            dropdownBtn.setAttribute('aria-expanded', String(nextState));
            dropdownWrapper.classList.toggle('is-open', nextState);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!dropdownWrapper.contains(e.target)) {
                dropdownBtn.setAttribute('aria-expanded', 'false');
                dropdownWrapper.classList.remove('is-open');
            }
        });

        // Keyboard navigation: Escape key closes the dropdown
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && dropdownWrapper.classList.contains('is-open')) {
                dropdownBtn.setAttribute('aria-expanded', 'false');
                dropdownWrapper.classList.remove('is-open');
                dropdownBtn.focus();
            }
        });

        // Close dropdown when a dropdown link is clicked (e.g. on mobile)
        dropdownMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                dropdownBtn.setAttribute('aria-expanded', 'false');
                dropdownWrapper.classList.remove('is-open');
                if (mainNav) {
                    mainNav.classList.remove('is-open');
                    if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }

    // 3. Product Gallery Thumbnail Switcher
    const mainImage = document.getElementById('product-main-img');
    const thumbnails = document.querySelectorAll('.gallery-thumb-btn');

    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(btn => {
            btn.addEventListener('click', function () {
                const newSrc = this.getAttribute('data-img-src');
                const newAlt = this.getAttribute('data-img-alt');
                if (newSrc) {
                    mainImage.setAttribute('src', newSrc);
                    if (newAlt) mainImage.setAttribute('alt', newAlt);
                    thumbnails.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                }
            });
        });
    }

    // 4. Smooth scrolling for hash anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // 5. Ghi nhận lượt bấm Affiliate an toàn (Direct Link Tracking)
    // - Chỉ ghi nhận cho liên kết trực tiếp (link_mode = 'direct'); liên kết 'redirect' do server tự xử lý.
    // - Tuyệt đối KHÔNG chặn điều hướng (không dùng preventDefault, không gây trễ khi mở tab).
    // - Hạn chế gửi sự kiện lặp tức thời (Debounce 3 giây phía client).
    // - Dùng navigator.sendBeacon hoặc fetch keepalive không đồng bộ.
    const recentClicks = {};

    document.addEventListener('click', (e) => {
        const link = e.target.closest('a[data-track-click="true"]');
        if (!link) return;

        const offerId = link.getAttribute('data-offer-id');
        const linkMode = link.getAttribute('data-link-mode');

        // Nếu là chuyển hướng nội bộ (redirect), server đã tự ghi nhận trong redirect_offer_view
        if (linkMode !== 'direct') return;

        if (!offerId) return;

        const now = Date.now();
        // Client-side debounce 3 giây cho cùng một offer_id để tránh spam click đúp
        if (recentClicks[offerId] && now - recentClicks[offerId] < 3000) {
            return;
        }
        recentClicks[offerId] = now;

        const payload = {
            offer_id: parseInt(offerId, 10),
            referrer_path: window.location.pathname
        };

        const targetApi = '/analytics/api/click/';

        try {
            if (navigator.sendBeacon) {
                const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
                const sent = navigator.sendBeacon(targetApi, blob);
                if (sent) return;
            }

            // Fallback sang fetch với keepalive nếu sendBeacon trả về false hoặc không hỗ trợ
            if (window.fetch) {
                fetch(targetApi, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                    keepalive: true
                }).catch(() => {
                    // Lỗi tracking hoàn toàn âm thầm, không ảnh hưởng đến điều hướng của độc giả
                });
            }
        } catch (err) {
            // Chịu lỗi tuyệt đối: không để ngoại lệ JS làm gián đoạn hành vi người dùng
        }
    });
});

