import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from core.models import Project, Article, TradingArticle, MqlProduct, BrokerAd, Message, Lead, SiteVisitor, AdminSettings, db
from core import translator
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text, func
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# دالة رفع الصور
def save_uploaded_image(file_obj):
    if file_obj and file_obj.filename:
        filename = secure_filename(file_obj.filename)
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file_obj.save(file_path)
        return url_for('static', filename=f'uploads/{filename}')
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: 
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# ================= مسارات لوحة التحكم الشاملة =================
@admin_bp.route('/admin', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        status = request.form.get('status', 'published')
        publish_at_str = request.form.get('publish_at', '')
        publish_at = datetime.strptime(publish_at_str, '%Y-%m-%dT%H:%M') if status == 'scheduled' and publish_at_str else datetime.utcnow() + timedelta(hours=3)

        # رفع الصورة إذا وجدت
        file_upload = request.files.get('image_file')
        uploaded_url = save_uploaded_image(file_upload)

        if form_type == 'project':
            icon_val = uploaded_url if uploaded_url else request.form['icon']
            title_ar = request.form['title']
            desc_ar = request.form['description']
            full_ar = request.form['full_details']
            new_project = Project(
                title=title_ar, title_en=translator.translate(title_ar),
                description=desc_ar, description_en=translator.translate(desc_ar),
                full_details=full_ar, full_details_en=translator.translate(full_ar),
                technologies=request.form['technologies'], icon=icon_val, status=status, publish_at=publish_at
            )
            db.session.add(new_project)
            
        elif form_type == 'article':
            image_val = uploaded_url if uploaded_url else request.form.get('image', '')
            title_ar = request.form['title']
            sum_ar = request.form['summary']
            cont_ar = request.form['content']
            new_article = Article(
                title=title_ar, title_en=translator.translate(title_ar),
                summary=sum_ar, summary_en=translator.translate(sum_ar),
                content=cont_ar, content_en=translator.translate(cont_ar),
                image=image_val, status=status, publish_at=publish_at
            )
            db.session.add(new_article)
            
        elif form_type == 'trading_article':
            image_val = uploaded_url if uploaded_url else request.form.get('image', '')
            title_ar = request.form['title']
            sum_ar = request.form['summary']
            cont_ar = request.form['content']
            new_t_article = TradingArticle(
                title=title_ar, title_en=translator.translate(title_ar),
                summary=sum_ar, summary_en=translator.translate(sum_ar),
                content=cont_ar, content_en=translator.translate(cont_ar),
                image=image_val, status=status, publish_at=publish_at
            )
            db.session.add(new_t_article)
            
        elif form_type == 'mql_product':
            icon_val = uploaded_url if uploaded_url else request.form.get('icon', '')
            name_ar = request.form['name']
            desc_ar = request.form['description']
            new_product = MqlProduct(
                name=name_ar, name_en=translator.translate(name_ar),
                description=desc_ar, description_en=translator.translate(desc_ar),
                price=request.form['price'], mql_url=request.form['mql_url'], icon=icon_val
            )
            db.session.add(new_product)
            
        elif form_type == 'broker_ad':
            image_val = uploaded_url if uploaded_url else request.form.get('image_url', '')
            new_ad = BrokerAd(
                name=request.form['name'], url=request.form['url'],
                image_url=image_val, display_order=int(request.form.get('order', 0))
            )
            db.session.add(new_ad)

        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    
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
    
    return render_template('admin/admin.html', 
                           projects=projects, articles=articles, trading_articles=trading_articles, 
                           mql_products=mql_products, broker_ads=broker_ads, messages=messages, leads=leads, 
                           unread=unread_count, total_visitors=total_visitors, today_visitors=today_visitors, 
                           yesterday_visitors=yesterday_visitors, source_stats=source_stats, country_stats=country_stats)

# ================= نظام الأمان وتسجيل الدخول =================
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    # التأكد من وجود أدمن افتراضي
    admin_user = AdminSettings.query.first()
    if not admin_user:
        admin_user = AdminSettings(username='admin', password_hash=generate_password_hash('mustafa2026'))
        db.session.add(admin_user)
        db.session.commit()

    if request.method == 'POST':
        if request.form['username'] == admin_user.username and check_password_hash(admin_user.password_hash, request.form['password']):
            session['logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        flash("بيانات الدخول غير صحيحة")
    return render_template('shared/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('tech.home'))

@admin_bp.route('/admin/settings', methods=['POST'])
@login_required
def update_settings():
    admin_user = AdminSettings.query.first()
    new_user = request.form.get('new_username')
    new_pass = request.form.get('new_password')
    if new_user and new_pass:
        admin_user.username = new_user
        admin_user.password_hash = generate_password_hash(new_pass)
        db.session.commit()
        flash("تم تغيير بيانات الدخول بنجاح!")
    return redirect(url_for('admin.dashboard'))

# ================= عمليات التعديل الشاملة =================
@admin_bp.route('/edit_project/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    project = Project.query.get_or_404(id)
    if request.method == 'POST':
        project.title = request.form['title']
        project.description = request.form['description']
        project.full_details = request.form['full_details']
        project.technologies = request.form['technologies']
        project.status = request.form.get('status', 'published')
        
        uploaded_url = save_uploaded_image(request.files.get('image_file'))
        if uploaded_url: project.icon = uploaded_url
        elif request.form.get('icon'): project.icon = request.form.get('icon')
        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_project.html', project=project)

@admin_bp.route('/edit_article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)
    if request.method == 'POST':
        article.title = request.form['title']
        article.summary = request.form['summary']
        article.content = request.form['content']
        article.status = request.form.get('status', 'published')
        
        uploaded_url = save_uploaded_image(request.files.get('image_file'))
        if uploaded_url: article.image = uploaded_url
        elif request.form.get('image'): article.image = request.form.get('image')
        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_article.html', article=article)

@admin_bp.route('/edit_trading_article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_trading_article(id):
    article = TradingArticle.query.get_or_404(id)
    if request.method == 'POST':
        article.title = request.form['title']
        article.summary = request.form['summary']
        article.content = request.form['content']
        article.status = request.form.get('status', 'published')
        
        uploaded_url = save_uploaded_image(request.files.get('image_file'))
        if uploaded_url: article.image = uploaded_url
        elif request.form.get('image'): article.image = request.form.get('image')
        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_trading_article.html', article=article)

@admin_bp.route('/edit_mql_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_mql_product(id):
    prod = MqlProduct.query.get_or_404(id)
    if request.method == 'POST':
        prod.name = request.form['name']
        prod.description = request.form['description']
        prod.price = request.form['price']
        prod.mql_url = request.form['mql_url']
        uploaded_url = save_uploaded_image(request.files.get('image_file'))
        if uploaded_url: prod.icon = uploaded_url
        elif request.form.get('icon'): prod.icon = request.form.get('icon')
        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_mql_product.html', prod=prod)

@admin_bp.route('/edit_broker_ad/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_broker_ad(id):
    ad = BrokerAd.query.get_or_404(id)
    if request.method == 'POST':
        ad.name = request.form['name']
        ad.url = request.form['url']
        uploaded_url = save_uploaded_image(request.files.get('image_file'))
        if uploaded_url: ad.image_url = uploaded_url
        elif request.form.get('image_url'): ad.image_url = request.form.get('image_url')
        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_broker_ad.html', ad=ad)

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
    if item: item.is_visible = not item.is_visible
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