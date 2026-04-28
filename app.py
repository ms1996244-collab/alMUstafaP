from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
import hashlib
import urllib.request
import json
from sqlalchemy import text, func

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'al_mustafa_secure_2026_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# تشفير كلمة المرور في الذاكرة (حماية عسكرية)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('mustafa2026')

# ================= قاموس الترجمة المركزي (i18n) =================
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'lang_switch': 'EN', 'lang_code': 'en',
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
        'nav_home': 'Home', 'nav_about': 'About Us', 'nav_calc': 'Cost Calculator',
        'nav_portfolio': 'Portfolio', 'nav_blog': 'Blog', 'nav_contact': 'Contact Me',
        'hero_title': 'Luxury Digital Experiences', 'hero_subtitle': 'World-class full-stack software engineering for the Middle East.',
        'hero_cta': 'Calculate Your App Cost Now', 'calc_title': 'Smart App Cost Calculator',
        'calc_subtitle': 'Get an initial estimate for your project in seconds.',
        'calc_type_0': 'Choose App Type...', 'calc_type_1': 'Full E-commerce App',
        'calc_type_2': 'Corporate / Services App', 'calc_type_3': 'Delivery App (Client + Driver + Admin)',
        'calc_type_4': 'Financial Trading System / Bots', 'calc_design_0': 'Design Level...',
        'calc_design_1': 'Standard Design', 'calc_design_2': 'Luxury UI/UX Design',
        'calc_design_3': 'Extra Project Pages...', 'calc_est': 'The estimated cost for your project starts from:',
        'calc_input': 'Your phone or email to send the technical offer', 'calc_btn': 'Request Official Quote',
        'calc_success': 'Your request has been received! We will contact you soon.',
        'about_title': 'Why Al-Mustafa?',
        'about_text': 'We don\'t just write code; we build digital assets for companies. We specialize in luxury <strong>Flutter</strong> apps and trading systems, applying strict Clean Architecture to ensure your project\'s sustainability.',
        'partners_title': 'Success Partners', 'faq_title': 'Frequently Asked Questions',
        'faq_1_q': 'Do you upload the app to the stores?',
        'faq_1_a': 'Yes, absolutely. We handle uploading your app to Google Play and the App Store according to the latest acceptance policies.',
        'faq_2_q': 'What technologies do you use?',
        'faq_2_a': 'We rely on Google\'s Flutter framework to build fast cross-platform apps, using Supabase or Python for the backend to ensure maximum security and speed.',
        'faq_3_q': 'Is there technical support after delivery?',
        'faq_3_a': 'We offer a free technical support period after delivery to ensure the system is bug-free, with the possibility of signing a continuous maintenance contract.',
        'contact_title': 'Contact Me Directly', 'contact_name': 'Full Name',
        'contact_email': 'Email Address', 'contact_msg': 'How can I help you?',
        'contact_btn': 'Send Message', 'footer': '© 2026 Al-Mustafa Programming. All rights reserved.'
    }
}

# حقن الترجمة في جميع الصفحات تلقائياً
@app.context_processor
def inject_translations():
    lang = 'ar'
    if request.view_args and 'lang' in request.view_args:
        lang = request.view_args.get('lang', 'ar')
    elif request.path.startswith('/en/'):
        lang = 'en'
    if lang not in ['ar', 'en']: lang = 'ar'
    return dict(t=TRANSLATIONS[lang], current_lang=lang)
# ===============================================================

# --- الجداول الأساسية ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    full_details = db.Column(db.Text, nullable=True)
    technologies = db.Column(db.String(200), nullable=True)
    icon = db.Column(db.String(200), default='fas fa-code')
    is_visible = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    summary = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

with app.app_context():
    db.create_all() 
    update_queries = [
        "ALTER TABLE project ADD COLUMN is_visible BOOLEAN DEFAULT 1",
        "ALTER TABLE article ADD COLUMN is_visible BOOLEAN DEFAULT 1",
        "ALTER TABLE project ADD COLUMN views INTEGER DEFAULT 0",
        "ALTER TABLE article ADD COLUMN views INTEGER DEFAULT 0",
        "ALTER TABLE article ADD COLUMN likes INTEGER DEFAULT 0",
        "ALTER TABLE site_visitor ADD COLUMN country VARCHAR(100) DEFAULT 'غير معروف'",
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
            if project_id: target = Project.query.get(project_id)
            else: target = Article.query.get(article_id)
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
            
            existing = SiteVisitor.query.filter_by(ip_hash=ip_hash, visit_date=today_iraq).first()
            if not existing:
                ref = request.referrer
                source_name = 'دخول مباشر'
                if ref:
                    if 'google' in ref: source_name = 'بحث Google'
                    elif 'linkedin' in ref: source_name = 'LinkedIn'
                    elif 'facebook' in ref: source_name = 'Facebook'
                    elif 't.co' in ref or 'twitter' in ref: source_name = 'Twitter / X'
                    else: source_name = ref 

                country_name = get_country_from_ip(clean_ip)
                db.session.add(SiteVisitor(ip_hash=ip_hash, visit_date=today_iraq, country=country_name, source=source_name))
                db.session.commit()

@app.route('/sitemap.xml')
def sitemap():
    projects = Project.query.filter_by(is_visible=True).all()
    articles = Article.query.filter_by(is_visible=True).all()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url>\n    <loc>{url_for("home", _external=True)}</loc>\n    <priority>1.0</priority>\n  </url>\n'
    xml += f'  <url>\n    <loc>{url_for("blog", _external=True)}</loc>\n    <priority>0.9</priority>\n  </url>\n'
    for p in projects: xml += f'  <url>\n    <loc>{url_for("project_details", id=p.id, _external=True)}</loc>\n    <priority>0.8</priority>\n  </url>\n'
    for a in articles: xml += f'  <url>\n    <loc>{url_for("article_details", id=a.id, _external=True)}</loc>\n    <priority>0.8</priority>\n  </url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    txt = "User-agent: *\nDisallow: /admin\nAllow: /\n"
    txt += f"Sitemap: {url_for('sitemap', _external=True)}"
    return Response(txt, mimetype='text/plain')

# تعديل الروابط لدعم اللغتين (SEO Routing)
@app.route('/')
@app.route('/<lang>/')
def home(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('home'))
    projects = Project.query.filter_by(is_visible=True).all()
    return render_template('index.html', projects=projects)

@app.route('/blog')
@app.route('/<lang>/blog')
def blog(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('blog'))
    articles = Article.query.filter_by(is_visible=True).order_by(Article.created_at.desc()).all()
    return render_template('blog.html', articles=articles)

@app.route('/project/<int:id>')
@app.route('/<lang>/project/<int:id>')
def project_details(id, lang='ar'):
    project = Project.query.get_or_404(id)
    if not project.is_visible and 'logged_in' not in session: return redirect(url_for('home'))
    update_unique_view(project_id=id)
    prev_project = Project.query.filter(Project.id < id, Project.is_visible == True).order_by(Project.id.desc()).first()
    next_project = Project.query.filter(Project.id > id, Project.is_visible == True).order_by(Project.id.asc()).first()
    return render_template('project_details.html', project=project, prev_project=prev_project, next_project=next_project)

@app.route('/article/<int:id>')
@app.route('/<lang>/article/<int:id>')
def article_details(id, lang='ar'):
    article = Article.query.get_or_404(id)
    if not article.is_visible and 'logged_in' not in session: return redirect(url_for('home'))
    update_unique_view(article_id=id)
    return render_template('article_details.html', article=article)

@app.route('/like_article/<int:id>', methods=['POST'])
def like_article(id):
    article = Article.query.get_or_404(id)
    article.likes = (article.likes or 0) + 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': article.likes})

@app.route('/contact', methods=['POST'])
def contact():
    new_msg = Message(name=request.form.get('name'), email=request.form.get('email'), phone=request.form.get('phone'), content=request.form.get('content'))
    db.session.add(new_msg)
    db.session.commit()
    flash("Message Sent! رسالتك وصلت بنجاح.")
    return redirect(url_for('home'))

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    new_lead = Lead(
        contact_info=request.form.get('contact_info'),
        app_type=request.form.get('app_type'),
        estimated_price=request.form.get('estimated_price')
    )
    db.session.add(new_lead)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_attempts' not in session: session['login_attempts'] = 0
    if session['login_attempts'] >= 5:
        flash("تم حظر محاولات الدخول مؤقتاً لأسباب أمنية.")
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
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

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'project':
            new_project = Project(title=request.form['title'], description=request.form['description'], full_details=request.form['full_details'], technologies=request.form['technologies'], icon=request.form['icon'])
            db.session.add(new_project)
        elif form_type == 'article':
            new_article = Article(title=request.form['title'], summary=request.form['summary'], content=request.form['content'], image=request.form['image'])
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
        article.image = request.form['image']
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_article.html', article=article)

@app.route('/toggle_visibility/<string:type>/<int:id>')
@login_required
def toggle_visibility(type, id):
    if type == 'project': item = Project.query.get_or_404(id)
    else: item = Article.query.get_or_404(id)
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
    if type == 'msg': item = Message.query.get_or_404(id)
    else: item = Lead.query.get_or_404(id)
    item.is_read = True
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)