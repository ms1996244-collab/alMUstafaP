from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
import hashlib
import urllib.request
import json
from sqlalchemy import text, func
from deep_translator import GoogleTranslator

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'al_mustafa_secure_2026_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ================= بيانات الدخول والحماية =================
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('mustafa2026')

translator = GoogleTranslator(source='ar', target='en')

# --- الجداول المطورة لدعم اللغتين ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    title_en = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text)
    full_details = db.Column(db.Text, nullable=True)
    full_details_en = db.Column(db.Text)
    technologies = db.Column(db.String(200), nullable=True)
    icon = db.Column(db.String(200), default='fas fa-code')
    is_visible = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    title_en = db.Column(db.String(150))
    summary = db.Column(db.String(300), nullable=False)
    summary_en = db.Column(db.String(300))
    content = db.Column(db.Text, nullable=False)
    content_en = db.Column(db.Text)
    image = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_visible = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)

class ViewTracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_hash = db.Column(db.String(128), nullable=False)
    project_id = db.Column(db.Integer, nullable=True)
    article_id = db.Column(db.Integer, nullable=True)
    view_date = db.Column(db.Date, nullable=False, default=date.today)

class SiteVisitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_hash = db.Column(db.String(128), nullable=False)
    visit_date = db.Column(db.Date, nullable=False, default=date.today)
    country = db.Column(db.String(100), default='غير معروف')
    source = db.Column(db.String(255), default='دخول مباشر')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(25), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_info = db.Column(db.String(150), nullable=False)
    app_type = db.Column(db.String(100), nullable=False)
    estimated_price = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

# ================= دالة الحماية =================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

## ================= قاموس الترجمة المركزي (مع تحسينات الـ SEO) =================
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'lang_switch': 'EN', 'lang_code': 'en',
        # --- SEO Meta Descriptions ---
        'meta_desc_home': 'تبحث عن مبرمج فلاتر محترف؟ مصطفى علي، مهندس برمجيات متخصص في بناء تطبيقات الموبايل الفاخرة وأنظمة التداول الآلي (SMC) بمعايير Clean Architecture. اطلب تسعيرة مشروعك الآن.',
        'meta_desc_blog': 'مدونة تقنية متخصصة في هندسة البرمجيات، تطوير تطبيقات Flutter، وبرمجة استراتيجيات التداول الذكية. مقالات وشروحات برمجية متقدمة للمطورين ورواد الأعمال.',
        # ------------------------------
        'nav_home': 'الرئيسية', 'nav_about': 'عنا', 'nav_calc': 'حاسبة التكلفة',
        'nav_portfolio': 'سجل الإنجازات', 'nav_blog': 'المدونة', 'nav_contact': 'تواصل معي',
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
        'about_text': 'نحن لا نكتب أكواداً فقط، بل نبني أصولاً رقمية للشركات. تخصصنا في تطبيقات <strong>Flutter</strong> الفاخرة وأنظمة التداول، مع تطبيق صارم لهيكلية Clean Architecture لضمان استدامة مشروعك.',
        'partners_title': 'شركاء النجاح', 'faq_title': 'الأسئلة الشائعة',
        'faq_1_q': 'هل توفرون خدمة رفع التطبيق على المتاجر؟',
        'faq_1_a': 'نعم بالتأكيد، نحن نتكفل برفع تطبيقك على متجري Google Play و App Store وفق أحدث سياسات القبول، لتستلم مشروعك جاهزاً للإطلاق.',
        'faq_2_q': 'ما هي التقنيات المستخدمة في البرمجة؟',
        'faq_2_a': 'نعتمد على إطار عمل Flutter من جوجل لبرمجة تطبيقات سريعة تعمل على النظامين، مع استخدام Supabase أو Python للواجهة الخلفية (Backend) لضمان أعلى درجات الأمان والسرعة.',
        'faq_3_q': 'هل هناك دعم فني بعد التسليم؟',
        'faq_3_a': 'نقدم فترة دعم فني مجانية بعد التسليم لضمان خلو النظام من أي أخطاء، مع إمكانية توقيع عقد صيانة وتطوير مستمر حسب رغبتك.',
        'contact_title': 'تواصل معي المباشر', 'contact_name': 'الاسم الكريم',
        'contact_email': 'البريد الإلكتروني', 'contact_msg': 'كيف يمكنني مساعدتك؟',
        'contact_btn': 'إرسال الرسالة', 'footer': '© 2026 Al-Mustafa Programming. All rights reserved.'
    },
    'en': {
        'dir': 'ltr', 'lang_switch': 'العربية', 'lang_code': 'ar',
        # --- SEO Meta Descriptions ---
        'meta_desc_home': 'Looking for an expert Flutter developer? Mustafa Ali specializes in luxury mobile apps and automated trading systems (SMC) using Clean Architecture. Get your quote now.',
        'meta_desc_blog': 'A tech blog dedicated to software engineering, Flutter development, and smart trading strategies. Advanced insights for developers and entrepreneurs.',
        # ------------------------------
        'nav_home': 'Home', 'nav_about': 'About Us', 'nav_calc': 'Cost Calculator',
        'nav_portfolio': 'Portfolio', 'nav_blog': 'Blog', 'nav_contact': 'Contact Me',
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
        'about_text': 'We build digital assets using <strong>Flutter</strong> and Clean Architecture for sustainable, high-performance systems.',
        'partners_title': 'Partners', 'faq_title': 'FAQ',
        'faq_1_q': 'App store deployment?', 'faq_1_a': 'Yes, we handle App Store & Play Store publishing.',
        'faq_2_q': 'Technologies used?', 'faq_2_a': 'Flutter for cross-platform apps and Python/Supabase for backend.',
        'faq_3_q': 'Technical support?', 'faq_3_a': 'We offer post-delivery support and maintenance contracts.',
        'contact_title': 'Contact Me', 'contact_name': 'Name',
        'contact_email': 'Email', 'contact_msg': 'Message',
        'contact_btn': 'Send', 'footer': '© 2026 Al-Mustafa Programming.'
    }
}


@app.context_processor
def inject_translations():
    lang = 'ar'
    if request.view_args and 'lang' in request.view_args:
        lang = request.view_args.get('lang', 'ar')
    elif request.path.startswith('/en/'):
        lang = 'en'
    return dict(t=TRANSLATIONS.get(lang, TRANSLATIONS['ar']), current_lang=lang)

with app.app_context():
    db.create_all() 
    update_queries = [
        "ALTER TABLE project ADD COLUMN title_en VARCHAR(100)",
        "ALTER TABLE project ADD COLUMN description_en TEXT",
        "ALTER TABLE project ADD COLUMN full_details_en TEXT",
        "ALTER TABLE article ADD COLUMN title_en VARCHAR(150)",
        "ALTER TABLE article ADD COLUMN summary_en VARCHAR(300)",
        "ALTER TABLE article ADD COLUMN content_en TEXT",
        "ALTER TABLE site_visitor ADD COLUMN source VARCHAR(255) DEFAULT 'دخول مباشر'"
    ]
    for query in update_queries:
        try:
            db.session.execute(text(query))
            db.session.commit()
        except Exception:
            db.session.rollback()

def get_country_from_ip(ip):
    try:
        if ip.startswith(('127.', '192.168.', '10.')): return 'تصفح محلي'
        url = f"http://ip-api.com/json/{ip}?lang=ar"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            return data.get('country', 'غير معروف') if data.get('status') == 'success' else 'غير معروف'
    except: return 'غير معروف'

def update_unique_view(project_id=None, article_id=None):
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if raw_ip:
        clean_ip = raw_ip.split(',')[0].strip()
        ip_hash = hashlib.sha256(clean_ip.encode('utf-8')).hexdigest()
        today_iraq = (datetime.utcnow() + timedelta(hours=3)).date()
        viewed = ViewTracker.query.filter_by(ip_hash=ip_hash, project_id=project_id, article_id=article_id, view_date=today_iraq).first()
        if not viewed:
            target = Project.query.get(project_id) if project_id else Article.query.get(article_id)
            if target:
                target.views = (target.views or 0) + 1
                db.session.add(ViewTracker(ip_hash=ip_hash, project_id=project_id, article_id=article_id, view_date=today_iraq))
                db.session.commit()

@app.before_request
def track_visitor():
    if request.endpoint and not request.endpoint.startswith('static') and request.endpoint not in ['admin', 'login', 'logout']:
        raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if raw_ip:
            clean_ip = raw_ip.split(',')[0].strip()
            ip_hash = hashlib.sha256(clean_ip.encode('utf-8')).hexdigest()
            today_iraq = (datetime.utcnow() + timedelta(hours=3)).date()
            if not SiteVisitor.query.filter_by(ip_hash=ip_hash, visit_date=today_iraq).first():
                ref = request.referrer
                source_name = 'بحث Google' if ref and 'google' in ref else ('LinkedIn' if ref and 'linkedin' in ref else 'دخول مباشر')
                db.session.add(SiteVisitor(ip_hash=ip_hash, visit_date=today_iraq, country=get_country_from_ip(clean_ip), source=source_name))
                db.session.commit()

@app.route('/')
@app.route('/<lang>/')
def home(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('home'))
    projects_raw = Project.query.filter_by(is_visible=True).all()
    projects = []
    for p in projects_raw:
        p.display_title = p.title_en if lang == 'en' and p.title_en else p.title
        p.display_desc = p.description_en if lang == 'en' and p.description_en else p.description
        projects.append(p)
    return render_template('index.html', projects=projects)

@app.route('/blog')
@app.route('/<lang>/blog')
def blog(lang='ar'):
    articles_raw = Article.query.filter_by(is_visible=True).order_by(Article.created_at.desc()).all()
    articles = []
    for a in articles_raw:
        a.display_title = a.title_en if lang == 'en' and a.title_en else a.title
        a.display_summary = a.summary_en if lang == 'en' and a.summary_en else a.summary
        articles.append(a)
    return render_template('blog.html', articles=articles)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'project':
            title_ar = request.form['title']
            desc_ar = request.form['description']
            full_ar = request.form['full_details']
            
            title_en = translator.translate(title_ar)
            desc_en = translator.translate(desc_ar)
            full_en = translator.translate(full_ar)
            
            new_project = Project(
                title=title_ar, title_en=title_en,
                description=desc_ar, description_en=desc_en,
                full_details=full_ar, full_details_en=full_en,
                technologies=request.form['technologies'], icon=request.form['icon']
            )
            db.session.add(new_project)
            
        elif form_type == 'article':
            title_ar = request.form['title']
            sum_ar = request.form['summary']
            cont_ar = request.form['content']
            
            title_en = translator.translate(title_ar)
            sum_en = translator.translate(sum_ar)
            cont_en = translator.translate(cont_ar)
            
            new_article = Article(
                title=title_ar, title_en=title_en,
                summary=sum_ar, summary_en=sum_en,
                content=cont_ar, content_en=cont_en,
                image=request.form['image']
            )
            db.session.add(new_article)
        db.session.commit()
        return redirect(url_for('admin'))
    
    projects = Project.query.all()
    articles = Article.query.all()
    messages = Message.query.order_by(Message.id.desc()).all()
    leads = Lead.query.order_by(Lead.id.desc()).all()
    unread_count = Message.query.filter_by(is_read=False).count() + Lead.query.filter_by(is_read=False).count()
    today_iraq = (datetime.utcnow() + timedelta(hours=3)).date()
    yesterday_iraq = today_iraq - timedelta(days=1)
    today_visitors = SiteVisitor.query.filter_by(visit_date=today_iraq).count()
    yesterday_visitors = SiteVisitor.query.filter_by(visit_date=yesterday_iraq).count()
    total_visitors = SiteVisitor.query.count()
    source_stats = db.session.query(SiteVisitor.source, func.count(SiteVisitor.id)).group_by(SiteVisitor.source).order_by(func.count(SiteVisitor.id).desc()).all()
    country_stats = db.session.query(SiteVisitor.country, func.count(SiteVisitor.id)).group_by(SiteVisitor.country).order_by(func.count(SiteVisitor.id).desc()).all()
    monthly_stats = db.session.query(func.extract('year', SiteVisitor.visit_date).label('year'), func.extract('month', SiteVisitor.visit_date).label('month'), func.count(SiteVisitor.id)).group_by('year', 'month').order_by(text('year DESC, month DESC')).all()
    yearly_stats = db.session.query(func.extract('year', SiteVisitor.visit_date).label('year'), func.count(SiteVisitor.id)).group_by('year').order_by(text('year DESC')).all()
    return render_template('admin.html', projects=projects, articles=articles, messages=messages, leads=leads, unread=unread_count, total_visitors=total_visitors, today_visitors=today_visitors, yesterday_visitors=yesterday_visitors, source_stats=source_stats, country_stats=country_stats, monthly_stats=monthly_stats, yearly_stats=yearly_stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_attempts' not in session: session['login_attempts'] = 0
    if session['login_attempts'] >= 5:
        flash("تم حظر محاولات الدخول مؤقتاً لأسباب أمنية.")
        return render_template('login.html')
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, request.form['password']):
            session['logged_in'] = True
            session['login_attempts'] = 0 
            return redirect(url_for('admin'))
        session['login_attempts'] += 1
        flash("بيانات الدخول غير صحيحة")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/project/<int:id>')
@app.route('/<lang>/project/<int:id>')
def project_details(id, lang='ar'):
    project = Project.query.get_or_404(id)
    update_unique_view(project_id=id)
    project.display_title = project.title_en if lang == 'en' and project.title_en else project.title
    project.display_full = project.full_details_en if lang == 'en' and project.full_details_en else project.full_details
    return render_template('project_details.html', project=project)

@app.route('/article/<int:id>')
@app.route('/<lang>/article/<int:id>')
def article_details(id, lang='ar'):
    article = Article.query.get_or_404(id)
    update_unique_view(article_id=id)
    article.display_title = article.title_en if lang == 'en' and article.title_en else article.title
    article.display_content = article.content_en if lang == 'en' and article.content_en else article.content
    return render_template('article_details.html', article=article)

# ================= الدوال المستعادة (Edit) =================
@app.route('/edit_project/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    project = Project.query.get_or_404(id)
    if request.method == 'POST':
        project.title = request.form['title']
        project.description = request.form['description']
        project.full_details = request.form['full_details']
        project.technologies = request.form['technologies']
        project.icon = request.form['icon']
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_project.html', project=project)

@app.route('/edit_article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)
    if request.method == 'POST':
        article.title = request.form['title']
        article.summary = request.form['summary']
        article.content = request.form['content']
        article.image = request.form.get('image', '')
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_article.html', article=article)

# ================= بقية مسارات العمليات =================
@app.route('/contact', methods=['POST'])
def contact():
    new_msg = Message(name=request.form.get('name'), email=request.form.get('email'), phone=request.form.get('phone'), content=request.form.get('content'))
    db.session.add(new_msg)
    db.session.commit()
    flash("Message Sent! وصلت رسالتك.")
    return redirect(url_for('home'))

@app.route('/like_article/<int:id>', methods=['POST'])
def like_article(id):
    article = Article.query.get_or_404(id)
    article.likes = (article.likes or 0) + 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': article.likes})

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    new_lead = Lead(contact_info=request.form.get('contact_info'), app_type=request.form.get('app_type'), estimated_price=request.form.get('estimated_price'))
    db.session.add(new_lead)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/toggle_visibility/<string:type>/<int:id>')
@login_required
def toggle_visibility(type, id):
    item = Project.query.get_or_404(id) if type == 'project' else Article.query.get_or_404(id)
    item.is_visible = not item.is_visible
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete/<string:type>/<int:id>')
@login_required
def delete_item(type, id):
    if type == 'project': db.session.delete(Project.query.get_or_404(id))
    elif type == 'lead': db.session.delete(Lead.query.get_or_404(id))
    else: db.session.delete(Article.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/read/<string:type>/<int:id>')
@login_required
def mark_read(type, id):
    item = Message.query.get_or_404(id) if type == 'msg' else Lead.query.get_or_404(id)
    item.is_read = True
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/sitemap.xml')
def sitemap():
    projects = Project.query.filter_by(is_visible=True).all()
    articles = Article.query.filter_by(is_visible=True).all()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url><loc>{url_for("home", _external=True)}</loc><priority>1.0</priority></url>\n'
    for p in projects: xml += f'  <url><loc>{url_for("project_details", id=p.id, _external=True)}</loc></url>\n'
    for a in articles: xml += f'  <url><loc>{url_for("article_details", id=a.id, _external=True)}</loc></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    txt = "User-agent: *\nDisallow: /admin\nAllow: /\n"
    txt += f"Sitemap: {url_for('sitemap', _external=True)}"
    return Response(txt, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)