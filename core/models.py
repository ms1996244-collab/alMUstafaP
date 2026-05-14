from . import db
from datetime import datetime, date

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

# ================= 2. جداول قسم التداول والأسواق المالية (الجديدة) =================
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
    contact_info = db.Column(db.String(150), nullable=False) # تم التصحيح هنا
    app_type = db.Column(db.String(100), nullable=False)
    estimated_price = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)