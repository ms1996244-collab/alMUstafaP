from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'al_mustafa_secure_2026_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- الجداول ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    full_details = db.Column(db.Text, nullable=True)
    technologies = db.Column(db.String(200), nullable=True)
    icon = db.Column(db.String(200), default='fas fa-code')
    is_visible = db.Column(db.Boolean, default=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    summary = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_visible = db.Column(db.Boolean, default=True)

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
    db.create_all() # سيقوم بإنشاء جدول المقالات تلقائياً دون حذف مشاريعك

# --- مسارات الـ SEO ---
@app.route('/sitemap.xml')
def sitemap():
    projects = Project.query.filter_by(is_visible=True).all()
    articles = Article.query.filter_by(is_visible=True).all()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url>\n    <loc>{url_for("home", _external=True)}</loc>\n    <priority>1.0</priority>\n  </url>\n'
    for p in projects:
        xml += f'  <url>\n    <loc>{url_for("project_details", id=p.id, _external=True)}</loc>\n    <priority>0.8</priority>\n  </url>\n'
    for a in articles:
        xml += f'  <url>\n    <loc>{url_for("article_details", id=a.id, _external=True)}</loc>\n    <priority>0.9</priority>\n  </url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    txt = "User-agent: *\nDisallow: /admin\nAllow: /\n"
    txt += f"Sitemap: {url_for('sitemap', _external=True)}"
    return Response(txt, mimetype='text/plain')

# --- المسارات العامة ---
@app.route('/')
def home():
    projects = Project.query.filter_by(is_visible=True).all()
    articles = Article.query.filter_by(is_visible=True).order_by(Article.created_at.desc()).all()
    return render_template('index.html', projects=projects, articles=articles)

@app.route('/project/<int:id>')
def project_details(id):
    project = Project.query.get_or_404(id)
    if not project.is_visible and 'logged_in' not in session: return redirect(url_for('home'))
    prev_project = Project.query.filter(Project.id < id, Project.is_visible == True).order_by(Project.id.desc()).first()
    next_project = Project.query.filter(Project.id > id, Project.is_visible == True).order_by(Project.id.asc()).first()
    return render_template('project_details.html', project=project, prev_project=prev_project, next_project=next_project)

@app.route('/article/<int:id>')
def article_details(id):
    article = Article.query.get_or_404(id)
    if not article.is_visible and 'logged_in' not in session: return redirect(url_for('home'))
    return render_template('article_details.html', article=article)

@app.route('/contact', methods=['POST'])
def contact():
    new_msg = Message(name=request.form.get('name'), email=request.form.get('email'), phone=request.form.get('phone'), content=request.form.get('content'))
    db.session.add(new_msg)
    db.session.commit()
    flash("رسالتك وصلت بنجاح. سيتم التواصل معك قريباً.")
    return redirect(url_for('home'))

# --- الإدارة ---
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
    return render_template('admin.html', projects=projects, articles=articles, messages=messages, unread=unread_count)

# مسارات الحذف والإخفاء للمشاريع والمقالات
@app.route('/toggle_visibility/<string:type>/<int:id>')
@login_required
def toggle_visibility(type, id):
    if type == 'project':
        item = Project.query.get_or_404(id)
    else:
        item = Article.query.get_or_404(id)
    item.is_visible = not item.is_visible
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete/<string:type>/<int:id>')
@login_required
def delete_item(type, id):
    if type == 'project':
        db.session.delete(Project.query.get_or_404(id))
    else:
        db.session.delete(Article.query.get_or_404(id))
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