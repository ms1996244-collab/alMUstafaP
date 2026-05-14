from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from core.models import Project, Article, TradingArticle, MqlProduct, BrokerAd, Message, Lead, SiteVisitor, db
from core import translator
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from sqlalchemy import text, func
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# ================= بيانات الدخول والحماية =================
ADMIN_USERNAME = 'admin'
# لتسهيل الأمر هنا، نضع الـ hash المباشر أو يمكنك استيراده.
# في الإنتاج يفضل وضعه في ملف بيئة (environment variables)
from werkzeug.security import generate_password_hash
ADMIN_PASSWORD_HASH = generate_password_hash('mustafa2026')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: 
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# ================= مسارات لوحة التحكم =================
@admin_bp.route('/admin', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        status = request.form.get('status', 'published')
        publish_at_str = request.form.get('publish_at', '')
        
        if status == 'scheduled' and publish_at_str:
            publish_at = datetime.strptime(publish_at_str, '%Y-%m-%dT%H:%M')
        else:
            publish_at = datetime.utcnow() + timedelta(hours=3)

        # 1. قسم التكنولوجيا
        if form_type == 'project':
            title_ar = request.form['title']
            desc_ar = request.form['description']
            full_ar = request.form['full_details']
            new_project = Project(
                title=title_ar, title_en=translator.translate(title_ar),
                description=desc_ar, description_en=translator.translate(desc_ar),
                full_details=full_ar, full_details_en=translator.translate(full_ar),
                technologies=request.form['technologies'], icon=request.form['icon'],
                status=status, publish_at=publish_at
            )
            db.session.add(new_project)
            
        elif form_type == 'article':
            title_ar = request.form['title']
            sum_ar = request.form['summary']
            cont_ar = request.form['content']
            new_article = Article(
                title=title_ar, title_en=translator.translate(title_ar),
                summary=sum_ar, summary_en=translator.translate(sum_ar),
                content=cont_ar, content_en=translator.translate(cont_ar),
                image=request.form['image'],
                status=status, publish_at=publish_at
            )
            db.session.add(new_article)
            
        # 2. قسم التداول
        elif form_type == 'trading_article':
            title_ar = request.form['title']
            sum_ar = request.form['summary']
            cont_ar = request.form['content']
            new_t_article = TradingArticle(
                title=title_ar, title_en=translator.translate(title_ar),
                summary=sum_ar, summary_en=translator.translate(sum_ar),
                content=cont_ar, content_en=translator.translate(cont_ar),
                image=request.form['image'],
                status=status, publish_at=publish_at
            )
            db.session.add(new_t_article)
            
        elif form_type == 'mql_product':
            name_ar = request.form['name']
            desc_ar = request.form['description']
            new_product = MqlProduct(
                name=name_ar, name_en=translator.translate(name_ar),
                description=desc_ar, description_en=translator.translate(desc_ar),
                price=request.form['price'], mql_url=request.form['mql_url'],
                icon=request.form.get('icon', '')
            )
            db.session.add(new_product)
            
        elif form_type == 'broker_ad':
            new_ad = BrokerAd(
                name=request.form['name'], url=request.form['url'],
                image_url=request.form['image_url'], display_order=int(request.form.get('order', 0))
            )
            db.session.add(new_ad)

        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    
    # جلب البيانات لعرضها في لوحة التحكم
    projects = Project.query.order_by(Project.id.desc()).all()
    articles = Article.query.order_by(Article.id.desc()).all()
    trading_articles = TradingArticle.query.order_by(TradingArticle.id.desc()).all()
    mql_products = MqlProduct.query.order_by(MqlProduct.id.desc()).all()
    broker_ads = BrokerAd.query.order_by(BrokerAd.display_order.asc()).all()
    
    messages = Message.query.order_by(Message.id.desc()).all()
    leads = Lead.query.order_by(Lead.id.desc()).all()
    unread_count = Message.query.filter_by(is_read=False).count() + Lead.query.filter_by(is_read=False).count()
    
    # الإحصائيات
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
    
    return render_template('admin.html', 
                           projects=projects, articles=articles, 
                           trading_articles=trading_articles, mql_products=mql_products, broker_ads=broker_ads,
                           messages=messages, leads=leads, unread=unread_count, 
                           total_visitors=total_visitors, today_visitors=today_visitors, yesterday_visitors=yesterday_visitors, 
                           source_stats=source_stats, country_stats=country_stats, monthly_stats=monthly_stats, yearly_stats=yearly_stats, 
                           now_iraq=now_iraq)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_attempts' not in session: session['login_attempts'] = 0
    if session['login_attempts'] >= 5:
        flash("تم حظر محاولات الدخول مؤقتاً لأسباب أمنية.")
        return render_template('login.html')
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, request.form['password']):
            session['logged_in'] = True
            session['login_attempts'] = 0 
            return redirect(url_for('admin.dashboard'))
        session['login_attempts'] += 1
        flash("بيانات الدخول غير صحيحة")
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('tech.tech.home'))

# ================= عمليات الحذف والإخفاء والقراءة =================
@admin_bp.route('/toggle_visibility/<string:type>/<int:id>')
@login_required
def toggle_visibility(type, id):
    item = None
    if type == 'project': item = Project.query.get_or_404(id)
    elif type == 'article': item = Article.query.get_or_404(id)
    elif type == 'trading_article': item = TradingArticle.query.get_or_404(id)
    elif type == 'mql_product': item = MqlProduct.query.get_or_404(id)
    elif type == 'broker_ad': item = BrokerAd.query.get_or_404(id)
    
    if item:
        item.is_visible = not item.is_visible
        db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete/<string:type>/<int:id>')
@login_required
def delete_item(type, id):
    if type == 'project': db.session.delete(Project.query.get_or_404(id))
    elif type == 'article': db.session.delete(Article.query.get_or_404(id))
    elif type == 'trading_article': db.session.delete(TradingArticle.query.get_or_404(id))
    elif type == 'mql_product': db.session.delete(MqlProduct.query.get_or_404(id))
    elif type == 'broker_ad': db.session.delete(BrokerAd.query.get_or_404(id))
    elif type == 'lead': db.session.delete(Lead.query.get_or_404(id))
    
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/read/<string:type>/<int:id>')
@login_required
def mark_read(type, id):
    item = Message.query.get_or_404(id) if type == 'msg' else Lead.query.get_or_404(id)
    item.is_read = True
    db.session.commit()
    return redirect(url_for('admin.dashboard'))