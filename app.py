from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime, date
import hashlib
import urllib.request
import json
from sqlalchemy import text, func

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'al_mustafa_secure_2026_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    country = db.Column(db.String(100), default='غير معروف') # عمود الدولة الجديد

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(25), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
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
        "ALTER TABLE site_visitor ADD COLUMN country VARCHAR(100) DEFAULT 'غير معروف'"
    ]
    for query in update_queries:
        try:
            db.session.execute(text(query))
            db.session.commit()
        except Exception:
            db.session.rollback()

# --- خوارزمية جلب الدولة من الـ IP ---
def get_country_from_ip(ip):
    try:
        # تجنب البحث عن الآيبيات المحلية للسيرفر
        if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.'):
            return 'تصفح محلي'
        # جلب اسم الدولة باللغة العربية مع مهلة ثانيتين فقط لعدم إبطاء الموقع
        url = f"http://ip-api.com/json/{ip}?lang=ar"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            if data.get('status') == 'success':
                return data.get('country', 'غير معروف')
    except Exception:
        pass
    return 'غير معروف'

def update_unique_view(project_id=None, article_id=None):
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if raw_ip:
        clean_ip = raw_ip.split(',')[0].strip()
        ip_hash = hashlib.sha256(clean_ip.encode('utf-8')).hexdigest()
        today = date.today()
        viewed = ViewTracker.query.filter_by(ip_hash=ip_hash, project_id=project_id, article_id=article_id, view_date=today).first()
        if not viewed:
            if project_id: target = Project.query.get(project_id)
            else: target = Article.query.get(article_id)
            if target:
                target.views = (target.views or 0) + 1
                db.session.add(ViewTracker(ip_hash=ip_hash, project_id=project_id, article_id=article_id, view_date=today))
                db.session.commit()

@app.before_request
def track_visitor():
    if request.endpoint and not request.endpoint.startswith('static') and request.endpoint not in ['admin', 'login', 'logout']:
        raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if raw_ip:
            clean_ip = raw_ip.split(',')[0].strip()
            ip_hash = hashlib.sha256(clean_ip.encode('utf-8')).hexdigest()
            today = date.today()
            existing = SiteVisitor.query.filter_by(ip_hash=ip_hash, visit_date=today).first()
            if not existing:
                country_name = get_country_from_ip(clean_ip) # هنا نجلب الدولة!
                db.session.add(SiteVisitor(ip_hash=ip_hash, visit_date=today, country=country_name))
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

@app.route('/')
def home():
    projects = Project.query.filter_by(is_visible=True).all()
    return render_template('index.html', projects=projects)

@app.route('/blog')
def blog():
    articles = Article.query.filter_by(is_visible=True).order_by(Article.created_at.desc()).all()
    return render_template('blog.html', articles=articles)

@app.route('/project/<int:id>')
def project_details(id):
    project = Project.query.get_or_404(id)
    if not project.is_visible and 'logged_in' not in session: return redirect(url_for('home'))
    update_unique_view(project_id=id)
    prev_project = Project.query.filter(Project.id < id, Project.is_visible == True).order_by(Project.id.desc()).first()
    next_project = Project.query.filter(Project.id > id, Project.is_visible == True).order_by(Project.id.asc()).first()
    return render_template('project_details.html', project=project, prev_project=prev_project, next_project=next_project)

@app.route('/article/<int:id>')
def article_details(id):
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
    flash("رسالتك وصلت بنجاح. سيتم التواصل معك قريباً.")
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'mustafa2026':
            session['logged_in'] = True
            return redirect(url_for('admin'))
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
    unread_count = Message.query.filter_by(is_read=False).count()
    
    total_visitors = SiteVisitor.query.count()
    today_visitors = SiteVisitor.query.filter_by(visit_date=date.today()).count()
    
    # تجميع الزوار حسب الدولة (تحليل البيانات)
    country_stats = db.session.query(SiteVisitor.country, func.count(SiteVisitor.id)).group_by(SiteVisitor.country).order_by(func.count(SiteVisitor.id).desc()).all()
    
    return render_template('admin.html', projects=projects, articles=articles, messages=messages, unread=unread_count, total_visitors=total_visitors, today_visitors=today_visitors, country_stats=country_stats)

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
    else: db.session.delete(Article.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/read/<int:id>')
@login_required
def mark_read(id):
    msg = Message.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)