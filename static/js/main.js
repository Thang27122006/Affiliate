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
});
