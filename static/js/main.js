// 1. تأثير شريط التنقل عند التمرير
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(5, 5, 5, 0.85)';
        navbar.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.5)';
        navbar.style.padding = '15px 8%';
    } else {
        navbar.style.background = 'rgba(5, 5, 5, 0.7)';
        navbar.style.boxShadow = 'none';
        navbar.style.padding = '20px 8%';
    }
});

// 2. التمرير الناعم للروابط
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80,
                behavior: 'smooth'
            });
        }
    });
});

// 3. تفعيل قائمة الجوال
const menuBtn = document.getElementById('menu-btn');
const navLinks = document.getElementById('nav-links');
if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });
}
// 4. الأنيميشن والتفاعلات عند التمرير (Intersection Observer) - متكرر دائماً
document.addEventListener("DOMContentLoaded", () => {
    const observerOptions = {
        threshold: 0.1, // تفعيل التأثير عند ظهور 10% من العنصر
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // عند الدخول للشاشة: إظهار العنصر
                entry.target.classList.add('show-element');
            } else {
                // السر هنا: إخفاء العنصر عند الخروج من الشاشة ليعاد تشغيل الحركة لاحقاً
                entry.target.classList.remove('show-element');
            }
        });
    }, observerOptions);

    // تحديد كل العناصر التي نريد تطبيق تأثير الظهور عليها
    const elementsToAnimate = document.querySelectorAll('.project-card, .section-title, .hero-content, .contact-form, .admin-card, .details-container');

    elementsToAnimate.forEach(el => {
        el.classList.add('hidden-element'); // إخفاء العناصر مبدئياً
        observer.observe(el); // بدء المراقبة المستمرة
    });
});

// 5. تهيئة حقل الهاتف الذكي مع التعرف التلقائي على الدولة
const phoneInput = document.querySelector("#phone");
if (phoneInput) {
    window.intlTelInput(phoneInput, {
        initialCountry: "auto", // التعرف التلقائي
        geoIpLookup: function (success, failure) {
            fetch("https://ipapi.co/json") // خدمة التعرف على الـ IP
                .then(res => res.json())
                .then(data => success(data.country_code))
                .catch(() => success("iq")); // الافتراضي العراق إذا فشل التعرف
        },
        utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.19/js/utils.js"
    });
}

// 6. إخفاء رسالة الشكر تلقائياً بعد 5 ثوانٍ
const toast = document.getElementById('toast-notification');
if (toast) {
    setTimeout(() => {
        toast.classList.remove('show');
    }, 5000);
}