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
            menuToggle.setAttribute('aria-expanded', isOpen);
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!mainNav.contains(e.target) && !menuToggle.contains(e.target)) {
                mainNav.classList.remove('is-open');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // 2. Product Gallery Thumbnail Switcher
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

    // 3. Smooth scrolling for hash anchors
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
});
