from flask import request
from core import create_app, db
from sqlalchemy import text
from routes.tech_routes import tech_bp
from routes.trading_routes import trading_bp
from routes.admin_routes import admin_bp


# ================= قاموس الترجمة المحدث =================
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'lang_switch': 'EN', 'lang_code': 'en',
        'meta_desc_home': 'تبحث عن مبرمج فلاتر محترف؟ مصطفى علي، مهندس برمجيات متخصص في بناء تطبيقات الموبايل الفاخرة وأنظمة التداول الآلي (SMC).',
        'meta_desc_blog': 'مدونة تقنية متخصصة في هندسة البرمجيات، تطوير تطبيقات Flutter، وبرمجة استراتيجيات التداول الذكية.',
        'nav_home': 'الرئيسية', 'nav_about': 'عنا', 'nav_calc': 'حاسبة التكلفة',
        'nav_portfolio': 'سجل الإنجازات', 'nav_blog': 'المدونة', 'nav_contact': 'تواصل معي',
        'nav_trading': 'بوابة التداول',
        'hero_title': 'تجارب رقمية فاخرة', 'hero_subtitle': 'هندسة برمجية متكاملة بمعايير عالمية للشرق الأوسط',
        'hero_cta': 'احسب تكلفة تطبيقك الآن', 'calc_title': 'حاسبة تكلفة التطبيقات الذكية',
        'calc_subtitle': 'احصل على تسعير مبدئي لمشروعك في ثوانٍ معدودة.',
        'calc_type_0': 'اختر نوع التطبيق...', 'calc_type_1': 'تطبيق متجر إلكتروني متكامل',
        'calc_type_2': 'تطبيق شركة / خدمات', 'calc_type_3': 'تطبيق توصيل (عميل + مندوب + لوحة تحكم)',
        'calc_type_4': 'نظام تداول مالي / بوتات', 'calc_design_0': 'مستوى التصميم...',
        'calc_design_1': 'تصميم قياسي (Standard)', 'calc_design_2': 'تصميم فاخر ومخصص (Luxury UI/UX)',
        'calc_design_3': 'صفحات اضافيه للمشروع...', 'calc_est': 'التكلفة التقديرية لمشروعك تبدأ من:',
        'calc_input': 'رقم هاتفك أو بريدك لنرسل لك العرض الفني', 'calc_btn': 'طلب عرض سعر رسمي',
        'calc_success': 'تم استلام طلبك! سنتواصل معك قريباً.',
        'about_title': 'لماذا Al-Mustafa؟',
        'about_text': 'نحن لا نكتب أكواداً فقط، بل نبني أصولاً رقمية للشركات.',
        'partners_title': 'شركاء النجاح', 'faq_title': 'الأسئلة الشائعة',
        'faq_1_q': 'هل توفرون خدمة رفع التطبيق على المتاجر؟',
        'faq_1_a': 'نعم بالتأكيد، نحن نتكفل برفع تطبيقك على المتاجر.',
        'faq_2_q': 'ما هي التقنيات المستخدمة في البرمجة؟',
        'faq_2_a': 'نعتمد على إطار عمل Flutter و Python للواجهة الخلفية.',
        'faq_3_q': 'هل هناك دعم فني بعد التسليم؟',
        'faq_3_a': 'نقدم فترة دعم فني مجانية بعد التسليم.',
        'contact_title': 'تواصل معي المباشر', 'contact_name': 'الاسم الكريم',
        'contact_email': 'البريد الإلكتروني', 'contact_msg': 'كيف يمكنني مساعدتك؟',
        'contact_btn': 'إرسال الرسالة', 'footer': '© 2026 Al-Mustafa Programming. All rights reserved.'
    },
    'en': {
        'dir': 'ltr', 'lang_switch': 'العربية', 'lang_code': 'ar',
        'meta_desc_home': 'Looking for an expert Flutter developer? Mustafa Ali specializes in luxury mobile apps and SMC.',
        'meta_desc_blog': 'A tech blog dedicated to software engineering and smart trading strategies.',
        'nav_home': 'Home', 'nav_about': 'About Us', 'nav_calc': 'Cost Calculator',
        'nav_portfolio': 'Portfolio', 'nav_blog': 'Blog', 'nav_contact': 'Contact Me',
        'nav_trading': 'Trading Portal',
        'hero_title': 'Luxury Digital Experiences', 'hero_subtitle': 'World-class software engineering for the Middle East.',
        'hero_cta': 'Calculate Your App Cost Now', 'calc_title': 'Smart App Cost Calculator',
        'calc_subtitle': 'Get an initial estimate in seconds.',
        'calc_type_0': 'Choose App Type...', 'calc_type_1': 'E-commerce App',
        'calc_type_2': 'Corporate App', 'calc_type_3': 'Delivery App',
        'calc_type_4': 'Financial Bots', 'calc_design_0': 'Design Level...',
        'calc_design_1': 'Standard', 'calc_design_2': 'Luxury UI/UX',
        'calc_design_3': 'Extra Pages...', 'calc_est': 'The estimated cost starts from:',
        'calc_input': 'Email or phone for the offer', 'calc_btn': 'Request Quote',
        'calc_success': 'Request received! We will contact you.',
        'about_title': 'Why Al-Mustafa?',
        'about_text': 'We build digital assets using Flutter and Clean Architecture.',
        'partners_title': 'Partners', 'faq_title': 'FAQ',
        'faq_1_q': 'App store deployment?', 'faq_1_a': 'Yes, we handle App Store & Play Store publishing.',
        'faq_2_q': 'Technologies used?', 'faq_2_a': 'Flutter for cross-platform apps and Python/Supabase for backend.',
        'faq_3_q': 'Technical support?', 'faq_3_a': 'We offer post-delivery support.',
        'contact_title': 'Contact Me', 'contact_name': 'Name',
        'contact_email': 'Email', 'contact_msg': 'Message',
        'contact_btn': 'Send', 'footer': '© 2026 Al-Mustafa Programming.'
    }
}

app = create_app()

# دمج الترجمة على مستوى التطبيق
@app.context_processor
def inject_translations():
    lang = 'ar'
    if request.view_args and 'lang' in request.view_args:
        lang = request.view_args.get('lang', 'ar')
    elif request.path.startswith('/en/'):
        lang = 'en'
    return dict(t=TRANSLATIONS.get(lang, TRANSLATIONS['ar']), current_lang=lang)

# إنشاء الجداول عند التشغيل
with app.app_context():
    db.create_all()

# تسجيل المسارات (Blueprints)
app.register_blueprint(tech_bp)
app.register_blueprint(trading_bp)
app.register_blueprint(admin_bp) 

if __name__ == '__main__':
    app.run(debug=True)