from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from core.models import Project, Article, ViewTracker, SiteVisitor, Message, Lead, db
from core import translator
import hashlib
import urllib.request
import json
from datetime import datetime, date, timedelta

tech_bp = Blueprint('tech', __name__)

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
            target = None
            if project_id: target = Project.query.get(project_id)
            elif article_id: target = Article.query.get(article_id)
            
            if target:
                target.views = (target.views or 0) + 1
                db.session.add(ViewTracker(ip_hash=ip_hash, project_id=project_id, article_id=article_id, view_date=today_iraq))
                db.session.commit()

@tech_bp.before_request
def track_visitor():
    if request.endpoint and not request.endpoint.startswith('static') and request.endpoint not in ['admin.dashboard', 'admin.login', 'admin.logout']:
        raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if raw_ip:
            clean_ip = raw_ip.split(',')[0].strip()
            ip_hash = hashlib.sha256(clean_ip.encode('utf-8')).hexdigest()
            today_iraq = (datetime.utcnow() + timedelta(hours=3)).date()
            
            if not SiteVisitor.query.filter_by(ip_hash=ip_hash, visit_date=today_iraq).first():
                ref = request.referrer
                url_source = request.args.get('source') or request.args.get('utm_source')
                
                if url_source: source_name = f"رابط مخصص ({url_source})"
                elif ref:
                    ref_lower = ref.lower()
                    if 'google' in ref_lower: source_name = 'بحث Google'
                    elif 'bing' in ref_lower or 'yahoo' in ref_lower or 'duckduckgo' in ref_lower: source_name = 'محركات بحث أخرى'
                    elif 'linkedin' in ref_lower: source_name = 'LinkedIn'
                    elif 'facebook' in ref_lower or 'fb.com' in ref_lower: source_name = 'Facebook'
                    elif 'twitter' in ref_lower or 't.co' in ref_lower or 'x.com' in ref_lower: source_name = 'Twitter / X'
                    elif 'instagram' in ref_lower: source_name = 'Instagram'
                    else:
                        try: source_name = f"موقع آخر ({ref.split('/')[2]})"
                        except: source_name = 'موقع آخر'
                else: source_name = 'دخول مباشر / تطبيقات مراسلة'
                    
                db.session.add(SiteVisitor(ip_hash=ip_hash, visit_date=today_iraq, country=get_country_from_ip(clean_ip), source=source_name))
                db.session.commit()

# --- مسار البوابة المركزية (The Grand Hub) ---
@tech_bp.route('/')
@tech_bp.route('/<lang>/')
def tech.home(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('tech.tech.home'))
    return render_template('hub/index.html') # المسار المحدث

# --- مسار بوابة التقنية ---
@tech_bp.route('/tech')
@tech_bp.route('/<lang>/tech')
def tech_portal(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('tech.tech_portal'))
    now_iraq = datetime.utcnow() + timedelta(hours=3)
    projects_raw = Project.query.filter(Project.is_visible == True, (Project.status == 'published') | ((Project.status == 'scheduled') & (Project.publish_at <= now_iraq))).all()
    projects = []
    for p in projects_raw:
        p.display_title = p.title_en if lang == 'en' and p.title_en else p.title
        p.display_desc = p.description_en if lang == 'en' and p.description_en else p.description
        projects.append(p)
    return render_template('tech/tech.html', projects=projects) # المسار المحدث

@tech_bp.route('/tech.blog')
@tech_bp.route('/<lang>/tech.blog')
def tech.blog(lang='ar'):
    now_iraq = datetime.utcnow() + timedelta(hours=3)
    articles_raw = Article.query.filter(Article.is_visible == True, (Article.status == 'published') | ((Article.status == 'scheduled') & (Article.publish_at <= now_iraq))).order_by(Article.created_at.desc()).all()
    articles = []
    for a in articles_raw:
        a.display_title = a.title_en if lang == 'en' and a.title_en else a.title
        a.display_summary = a.summary_en if lang == 'en' and a.summary_en else a.summary
        articles.append(a)
    return render_template('tech/tech.blog.html', articles=articles) # المسار المحدث

@tech_bp.route('/project/<int:id>')
@tech_bp.route('/<lang>/project/<int:id>')
def tech.project_details(id, lang='ar'):
    project = Project.query.get_or_404(id)
    update_unique_view(project_id=id)
    project.display_title = project.title_en if lang == 'en' and project.title_en else project.title
    project.display_full = project.full_details_en if lang == 'en' and project.full_details_en else project.full_details
    return render_template('tech/tech.project_details.html', project=project) # المسار المحدث

@tech_bp.route('/article/<int:id>')
@tech_bp.route('/<lang>/article/<int:id>')
def tech.article_details(id, lang='ar'):
    article = Article.query.get_or_404(id)
    update_unique_view(article_id=id)
    article.display_title = article.title_en if lang == 'en' and article.title_en else article.title
    article.display_content = article.content_en if lang == 'en' and article.content_en else article.content
    return render_template('tech/tech.article_details.html', article=article) # المسار المحدث

@tech_bp.route('/tech.contact', methods=['POST'])
def tech.contact():
    new_msg = Message(name=request.form.get('name'), email=request.form.get('email'), phone=request.form.get('phone'), content=request.form.get('content'))
    db.session.add(new_msg)
    db.session.commit()
    flash("Message Sent! وصلت رسالتك.")
    return redirect(url_for('tech.tech.home'))

@tech_bp.route('/like_article/<int:id>', methods=['POST'])
def like_article(id):
    article = Article.query.get_or_404(id)
    article.likes = (article.likes or 0) + 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': article.likes})

@tech_bp.route('/submit_lead', methods=['POST'])
def submit_lead():
    new_lead = Lead(tech.contact_info=request.form.get('tech.contact_info'), app_type=request.form.get('app_type'), estimated_price=request.form.get('estimated_price'))
    db.session.add(new_lead)
    db.session.commit()
    return jsonify({'status': 'success'})

@tech_bp.route('/robots.txt')
def robots():
    txt = "User-agent: *\nDisallow: /admin\nAllow: /\n"
    txt += f"Sitemap: {url_for('tech.sitemap', _external=True)}"
    return Response(txt, mimetype='text/plain')
# --- صفحات المعلومات والتواصل المستقلة ---
@tech_bp.route('/about')
@tech_bp.route('/<lang>/about')
def about(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('tech.about'))
    return render_template('shared/about.html')

@tech_bp.route('/tech.contact-us')
@tech_bp.route('/<lang>/tech.contact-us')
def tech.contact_page(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('tech.tech.contact_page'))
    return render_template('shared/tech.contact.html')

@tech_bp.route('/sitemap.xml')
def sitemap():
    now_iraq = datetime.utcnow() + timedelta(hours=3)
    projects = Project.query.filter(Project.is_visible == True, (Project.status == 'published') | ((Project.status == 'scheduled') & (Project.publish_at <= now_iraq))).all()
    articles = Article.query.filter(Article.is_visible == True, (Article.status == 'published') | ((Article.status == 'scheduled') & (Article.publish_at <= now_iraq))).all()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url><loc>{url_for("tech.tech.home", _external=True)}</loc><priority>1.0</priority></url>\n'
    for p in projects: xml += f'  <url><loc>{url_for("tech.tech.project_details", id=p.id, _external=True)}</loc></url>\n'
    for a in articles: xml += f'  <url><loc>{url_for("tech.tech.article_details", id=a.id, _external=True)}</loc></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')