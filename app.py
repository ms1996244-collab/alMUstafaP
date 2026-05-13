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

# ================= 1. جداول قسم التكنولوجيا =================
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
    status = db.Column(db.String(20), default='published')
    publish_at = db.Column(db.DateTime, nullable=True)

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
    status = db.Column(db.String(20), default='published')
    publish_at = db.Column(db.DateTime, nullable=True)

# ================= 2. جداول قسم التداول والأسواق المالية =================
class TradingArticle(db.Model):
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
    status = db.Column(db.String(20), default='published')
    publish_at = db.Column(db.DateTime, nullable=True)

class MqlProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text)
    price = db.Column(db.String(50), nullable=False) 
    mql_url = db.Column(db.String(300), nullable=False) 
    icon = db.Column(db.String(250), nullable=True)
    is_visible = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)

class BrokerAd(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(300), nullable=False) 
    image_url = db.Column(db.String(250), nullable=False) 
    is_visible = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

# ================= 3. جداول التتبع والرسائل =================
class ViewTracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_hash = db.Column(db.String(128), nullable=False)
    project_id = db.Column(db.Integer, nullable=True)
    article_id = db.Column(db.Integer, nullable=True)
    trading_article_id = db.Column(db.Integer, nullable=True) 
    mql_product_id = db.Column(db.Integer, nullable=True)     
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

# ================= قاموس الترجمة =================
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'lang_switch': 'EN', 'lang_code': 'en',
        'meta_desc_home': 'تبحث عن مبرمج فلاتر محترف؟ مصطفى علي، مهندس برمجيات متخصص.',
        'meta_desc_blog': 'مدونة تقنية متخصصة.',
        'nav_home': 'الرئيسية', 'nav_about': 'عنا', 'nav_calc': 'حاسبة التكلفة',
        'nav_portfolio': 'سجل الإنجازات', 'nav_blog': 'المدونة', 'nav_contact': 'تواصل معي',
        'nav_trading': 'بوابة التداول',
        'hero_title': 'تجارب رقمية فاخرة', 'hero_subtitle': 'هندسة برمجية متكاملة بمعايير عالمية',
        'hero_cta': 'احسب تكلفة تطبيقك الآن', 'calc_title': 'حاسبة تكلفة التطبيقات الذكية',
        'calc_subtitle': 'احصل على تسعير مبدئي لمشروعك في ثوانٍ معدودة.',
        'calc_type_0': 'اختر نوع التطبيق...', 'calc_type_1': 'تطبيق متجر إلكتروني متكامل',
        'calc_type_2': 'تطبيق شركة / خدمات', 'calc_type_3': 'تطبيق توصيل (عميل + مندوب + لوحة تحكم)',
        'calc_type_4': 'نظام تداول مالي / بوتات', 'calc_design_0': 'مستوى التصميم...',
        'calc_design_1': 'تصميم قياسي (Standard)', 'calc_design_2': 'تصميم فاخر ومخصص (Luxury UI/UX)',
        'calc_design_3': 'صفحات اضافيه للمشروع...', 'calc_est': 'التكلفة التقديرية تبدأ من:',
        'calc_input': 'رقم هاتفك أو بريدك', 'calc_btn': 'طلب عرض سعر',
        'calc_success': 'تم استلام طلبك! سنتواصل معك قريباً.',
        'about_title': 'لماذا Al-Mustafa؟',
        'about_text': 'نبني أصولاً رقمية فاخرة.',
        'partners_title': 'شركاء النجاح', 'faq_title': 'الأسئلة الشائعة',
        'faq_1_q': 'هل توفرون خدمة الرفع؟', 'faq_1_a': 'نعم.',
        'faq_2_q': 'التقنيات المستخدمة؟', 'faq_2_a': 'نعتمد على Flutter.',
        'faq_3_q': 'هل يوجد دعم؟', 'faq_3_a': 'نعم يوجد.',
        'contact_title': 'تواصل معي المباشر', 'contact_name': 'الاسم الكريم',
        'contact_email': 'البريد الإلكتروني', 'contact_msg': 'الرسالة',
        'contact_btn': 'إرسال الرسالة', 'footer': '© 2026 Al-Mustafa.'
    },
    'en': {
        'dir': 'ltr', 'lang_switch': 'العربية', 'lang_code': 'ar',
        'meta_desc_home': 'Expert Flutter developer.',
        'meta_desc_blog': 'A tech blog.',
        'nav_home': 'Home', 'nav_about': 'About Us', 'nav_calc': 'Cost Calculator',
        'nav_portfolio': 'Portfolio', 'nav_blog': 'Blog', 'nav_contact': 'Contact Me',
        'nav_trading': 'Trading Portal',
        'hero_title': 'Luxury Digital Experiences', 'hero_subtitle': 'World-class software engineering',
        'hero_cta': 'Calculate Cost Now', 'calc_title': 'App Cost Calculator',
        'calc_subtitle': 'Get an initial estimate.',
        'calc_type_0': 'Choose App Type...', 'calc_type_1': 'E-commerce App',
        'calc_type_2': 'Corporate App', 'calc_type_3': 'Delivery App',
        'calc_type_4': 'Financial Bots', 'calc_design_0': 'Design Level...',
        'calc_design_1': 'Standard', 'calc_design_2': 'Luxury UI/UX',
        'calc_design_3': 'Extra Pages...', 'calc_est': 'Estimated cost starts from:',
        'calc_input': 'Email or phone', 'calc_btn': 'Request Quote',
        'calc_success': 'Request received!',
        'about_title': 'Why Us?',
        'about_text': 'We build digital assets.',
        'partners_title': 'Partners', 'faq_title': 'FAQ',
        'faq_1_q': 'Deployment?', 'faq_1_a': 'Yes.',
        'faq_2_q': 'Tech used?', 'faq_2_a': 'Flutter.',
        'faq_3_q': 'Support?', 'faq_3_a': 'Yes.',
        'contact_title': 'Contact Me', 'contact_name': 'Name',
        'contact_email': 'Email', 'contact_msg': 'Message',
        'contact_btn': 'Send', 'footer': '© 2026 Al-Mustafa.'
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

def get_country_from_ip(ip):
    try:
        if ip.startswith(('127.', '192.168.', '10.')): return 'تصفح محلي'
        url = f"http://ip-api.com/json/{ip}?lang=ar"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            return data.get('country', 'غير معروف') if data.get('status') == 'success' else 'غير معروف'
    except: return 'غير معروف'

def update_unique_view(project_id=None, article_id=None, trading_article_id=None, mql_product_id=None):
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if raw_ip:
        clean_ip = raw_ip.split(',')[0].strip()
        ip_hash = hashlib.sha256(clean_ip.encode('utf-8')).hexdigest()
        today_iraq = (datetime.utcnow() + timedelta(hours=3)).date()
        viewed = ViewTracker.query.filter_by(
            ip_hash=ip_hash, project_id=project_id, article_id=article_id, 
            trading_article_id=trading_article_id, mql_product_id=mql_product_id, view_date=today_iraq
        ).first()
        if not viewed:
            target = None
            if project_id: target = Project.query.get(project_id)
            elif article_id: target = Article.query.get(article_id)
            elif trading_article_id: target = TradingArticle.query.get(trading_article_id)
            elif mql_product_id: target = MqlProduct.query.get(mql_product_id)
            if target:
                target.views = (target.views or 0) + 1
                db.session.add(ViewTracker(ip_hash=ip_hash, project_id=project_id, article_id=article_id, trading_article_id=trading_article_id, mql_product_id=mql_product_id, view_date=today_iraq))
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
                source_name = 'دخول مباشر / تطبيقات مراسلة'
                db.session.add(SiteVisitor(ip_hash=ip_hash, visit_date=today_iraq, country=get_country_from_ip(clean_ip), source=source_name))
                db.session.commit()

# ================= 1. مسار الصفحة الرئيسية المركزية (The Grand Hub) =================
@app.route('/')
@app.route('/<lang>/')
def home(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('home'))
    return render_template('index.html')

# ================= 2. مسار بوابة التقنية (كانت الرئيسية سابقاً) =================
@app.route('/tech')
@app.route('/<lang>/tech')
def tech_portal(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('tech_portal'))
    now_iraq = datetime.utcnow() + timedelta(hours=3)
    projects_raw = Project.query.filter(Project.is_visible == True, (Project.status == 'published') | ((Project.status == 'scheduled') & (Project.publish_at <= now_iraq))).all()
    projects = []
    for p in projects_raw:
        p.display_title = p.title_en if lang == 'en' and p.title_en else p.title
        p.display_desc = p.description_en if lang == 'en' and p.description_en else p.description
        projects.append(p)
    return render_template('tech.html', projects=projects)

# ================= 3. مسار بوابة التداول =================
@app.route('/trading')
@app.route('/<lang>/trading')
def trading_portal(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('trading_portal'))
    now_iraq = datetime.utcnow() + timedelta(hours=3)
    trading_articles_raw = TradingArticle.query.filter(TradingArticle.is_visible == True, (TradingArticle.status == 'published') | ((TradingArticle.status == 'scheduled') & (TradingArticle.publish_at <= now_iraq))).order_by(TradingArticle.created_at.desc()).all()
    trading_articles = []
    for a in trading_articles_raw:
        a.display_title = a.title_en if lang == 'en' and a.title_en else a.title
        a.display_summary = a.summary_en if lang == 'en' and a.summary_en else a.summary
        trading_articles.append(a)
        
    mql_products_raw = MqlProduct.query.filter_by(is_visible=True).all()
    mql_products = []
    for p in mql_products_raw:
        p.display_name = p.name_en if lang == 'en' and p.name_en else p.name
        p.display_desc = p.description_en if lang == 'en' and p.description_en else p.description
        mql_products.append(p)
        
    broker_ads = BrokerAd.query.filter_by(is_visible=True).order_by(BrokerAd.display_order.asc()).all()
    return render_template('trading_portal.html', articles=trading_articles, products=mql_products, brokers=broker_ads)

@app.route('/blog')
@app.route('/<lang>/blog')
def blog(lang='ar'):
    now_iraq = datetime.utcnow() + timedelta(hours=3)
    articles_raw = Article.query.filter(Article.is_visible == True, (Article.status == 'published') | ((Article.status == 'scheduled') & (Article.publish_at <= now_iraq))).order_by(Article.created_at.desc()).all()
    articles = []
    for a in articles_raw:
        a.display_title = a.title_en if lang == 'en' and a.title_en else a.title
        a.display_summary = a.summary_en if lang == 'en' and a.summary_en else a.summary
        articles.append(a)
    return render_template('blog.html', articles=articles)

# ================= مسارات لوحة التحكم (Admin) =================
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        status = request.form.get('status', 'published')
        publish_at_str = request.form.get('publish_at', '')
        if status == 'scheduled' and publish_at_str: publish_at = datetime.strptime(publish_at_str, '%Y-%m-%dT%H:%M')
        else: publish_at = datetime.utcnow() + timedelta(hours=3)

        if form_type == 'project':
            title_ar = request.form['title']
            db.session.add(Project(title=title_ar, title_en=translator.translate(title_ar), description=request.form['description'], description_en=translator.translate(request.form['description']), full_details=request.form['full_details'], full_details_en=translator.translate(request.form['full_details']), technologies=request.form['technologies'], icon=request.form['icon'], status=status, publish_at=publish_at))
        elif form_type == 'article':
            title_ar = request.form['title']
            db.session.add(Article(title=title_ar, title_en=translator.translate(title_ar), summary=request.form['summary'], summary_en=translator.translate(request.form['summary']), content=request.form['content'], content_en=translator.translate(request.form['content']), image=request.form.get('image', ''), status=status, publish_at=publish_at))
        elif form_type == 'trading_article':
            title_ar = request.form['title']
            db.session.add(TradingArticle(title=title_ar, title_en=translator.translate(title_ar), summary=request.form['summary'], summary_en=translator.translate(request.form['summary']), content=request.form['content'], content_en=translator.translate(request.form['content']), image=request.form.get('image', ''), status=status, publish_at=publish_at))
        elif form_type == 'mql_product':
            name_ar = request.form['name']
            db.session.add(MqlProduct(name=name_ar, name_en=translator.translate(name_ar), description=request.form['description'], description_en=translator.translate(request.form['description']), price=request.form['price'], mql_url=request.form['mql_url'], icon=request.form.get('icon', '')))
        elif form_type == 'broker_ad':
            db.session.add(BrokerAd(name=request.form['name'], url=request.form['url'], image_url=request.form['image_url'], display_order=int(request.form.get('order', 0))))
        
        db.session.commit()
        return redirect(url_for('admin'))
    
    projects = Project.query.order_by(Project.id.desc()).all()
    articles = Article.query.order_by(Article.id.desc()).all()
    trading_articles = TradingArticle.query.order_by(TradingArticle.id.desc()).all()
    mql_products = MqlProduct.query.order_by(MqlProduct.id.desc()).all()
    broker_ads = BrokerAd.query.order_by(BrokerAd.display_order.asc()).all()
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
    now_iraq = datetime.utcnow() + timedelta(hours=3)
    
    return render_template('admin.html', projects=projects, articles=articles, trading_articles=trading_articles, mql_products=mql_products, broker_ads=broker_ads, messages=messages, leads=leads, unread=unread_count, total_visitors=total_visitors, today_visitors=today_visitors, yesterday_visitors=yesterday_visitors, source_stats=source_stats, country_stats=country_stats, monthly_stats=monthly_stats, yearly_stats=yearly_stats, now_iraq=now_iraq)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_attempts' not in session: session['login_attempts'] = 0
    if session['login_attempts'] >= 5: return render_template('login.html')
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, request.form['password']):
            session['logged_in'] = True
            session['login_attempts'] = 0 
            return redirect(url_for('admin'))
        session['login_attempts'] += 1
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

@app.route('/trading_article/<int:id>')
@app.route('/<lang>/trading_article/<int:id>')
def trading_article_details(id, lang='ar'):
    article = TradingArticle.query.get_or_404(id)
    update_unique_view(trading_article_id=id)
    article.display_title = article.title_en if lang == 'en' and article.title_en else article.title
    article.display_content = article.content_en if lang == 'en' and article.content_en else article.content
    return render_template('trading_article_details.html', article=article) 

@app.route('/mql_product/<int:id>/click')
def mql_product_click(id):
    product = MqlProduct.query.get_or_404(id)
    update_unique_view(mql_product_id=id)
    return redirect(product.mql_url)

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
        project.status = request.form.get('status', 'published')
        publish_at_str = request.form.get('publish_at', '')
        if project.status == 'scheduled' and publish_at_str: project.publish_at = datetime.strptime(publish_at_str, '%Y-%m-%dT%H:%M')
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
        article.status = request.form.get('status', 'published')
        publish_at_str = request.form.get('publish_at', '')
        if article.status == 'scheduled' and publish_at_str: article.publish_at = datetime.strptime(publish_at_str, '%Y-%m-%dT%H:%M')
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('edit_article.html', article=article)

@app.route('/contact', methods=['POST'])
def contact():
    db.session.add(Message(name=request.form.get('name'), email=request.form.get('email'), phone=request.form.get('phone'), content=request.form.get('content')))
    db.session.commit()
    flash("Message Sent! وصلت رسالتك.")
    return redirect(url_for('home'))

@app.route('/like_article/<int:id>', methods=['POST'])
def like_article(id):
    article = Article.query.get_or_404(id)
    article.likes = (article.likes or 0) + 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': article.likes})

@app.route('/like_trading_article/<int:id>', methods=['POST'])
def like_trading_article(id):
    article = TradingArticle.query.get_or_404(id)
    article.likes = (article.likes or 0) + 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': article.likes})

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    db.session.add(Lead(contact_info=request.form.get('contact_info'), app_type=request.form.get('app_type'), estimated_price=request.form.get('estimated_price')))
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/toggle_visibility/<string:type>/<int:id>')
@login_required
def toggle_visibility(type, id):
    if type == 'project': item = Project.query.get_or_404(id)
    elif type == 'article': item = Article.query.get_or_404(id)
    elif type == 'trading_article': item = TradingArticle.query.get_or_404(id)
    elif type == 'mql_product': item = MqlProduct.query.get_or_404(id)
    elif type == 'broker_ad': item = BrokerAd.query.get_or_404(id)
    item.is_visible = not item.is_visible
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete/<string:type>/<int:id>')
@login_required
def delete_item(type, id):
    if type == 'project': db.session.delete(Project.query.get_or_404(id))
    elif type == 'article': db.session.delete(Article.query.get_or_404(id))
    elif type == 'trading_article': db.session.delete(TradingArticle.query.get_or_404(id))
    elif type == 'mql_product': db.session.delete(MqlProduct.query.get_or_404(id))
    elif type == 'broker_ad': db.session.delete(BrokerAd.query.get_or_404(id))
    elif type == 'lead': db.session.delete(Lead.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/read/<string:type>/<int:id>')
@login_required
def mark_read(type, id):
    item = Message.query.get_or_404(id) if type == 'msg' else Lead.query.get_or_404(id)
    item.is_read = True
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)