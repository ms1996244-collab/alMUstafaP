from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from core.models import TradingArticle, MqlProduct, BrokerAd, ViewTracker, TradingNews, db
from core import translator
import hashlib
from datetime import datetime, timedelta
import urllib.request
import xml.etree.ElementTree as ET
import re

trading_bp = Blueprint('trading', __name__)

# --- دالة تنظيف الأخبار من الأكواد الخبيثة ---
def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

# --- نظام الجلب والترجمة التلقائي (الروبوت الخفي) ---
def fetch_automated_news():
    try:
        # التحقق من آخر خبر لتجنب الإغراق (جلب جديد كل 3 ساعات فقط)
        last_news = TradingNews.query.order_by(TradingNews.created_at.desc()).first()
        now_iraq = datetime.utcnow() + timedelta(hours=3)
        
        if last_news and (now_iraq - last_news.created_at) < timedelta(hours=3):
            return # لم يحن وقت الجلب بعد

        # سحب الأخبار الحية للذهب والفوركس من Yahoo Finance
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F,EURUSD=X"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        channel = root.find('channel')
        
        count = 0
        for item in channel.findall('item'):
            if count >= 3: # نحتفظ بأهم 3 أخبار في كل سحبة
                break
                
            title_en = item.find('title').text
            desc_en_raw = item.find('description').text
            desc_en = clean_html(desc_en_raw) if desc_en_raw else ""
            
            # التأكد من عدم تكرار نفس الخبر في قاعدة البيانات
            existing = TradingNews.query.filter_by(title_en=title_en).first()
            if not existing:
                # الترجمة الفورية عبر نظامك الخاص
                title_ar = translator.translate(title_en)
                # نترجم أول 500 حرف كملخص للخبر لتسريع الأداء
                desc_ar = translator.translate(desc_en[:500]) + "..." if len(desc_en) > 10 else "تفاصيل الخبر متوفرة بالنسخة الإنجليزية."
                
                new_news = TradingNews(
                    title=title_ar,
                    title_en=title_en,
                    content=desc_ar,
                    content_en=desc_en,
                    created_at=now_iraq,
                    is_visible=True
                )
                db.session.add(new_news)
                count += 1
        
        if count > 0:
            db.session.commit()
            
    except Exception as e:
        print(f"Error Auto-Fetching News: {e}")
        pass

# --- نظام تتبع المشاهدات للمقالات والمنتجات ---
def update_trading_view(trading_article_id=None, mql_product_id=None):
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if raw_ip:
        clean_ip = raw_ip.split(',')[0].strip()
        ip_hash = hashlib.sha256(clean_ip.encode('utf-8')).hexdigest()
        today_iraq = (datetime.utcnow() + timedelta(hours=3)).date()
        
        viewed = ViewTracker.query.filter_by(
            ip_hash=ip_hash, 
            trading_article_id=trading_article_id,
            mql_product_id=mql_product_id,
            view_date=today_iraq
        ).first()
        
        if not viewed:
            target = None
            if trading_article_id: target = TradingArticle.query.get(trading_article_id)
            elif mql_product_id: target = MqlProduct.query.get(mql_product_id)
            
            if target:
                target.views = (target.views or 0) + 1
                db.session.add(ViewTracker(
                    ip_hash=ip_hash, 
                    trading_article_id=trading_article_id,
                    mql_product_id=mql_product_id,
                    view_date=today_iraq
                ))
                db.session.commit()

# --- مسارات بوابة التداول ---
@trading_bp.route('/trading')
@trading_bp.route('/<lang>/trading')
def trading_portal(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('trading.trading_portal'))
    
    # تشغيل روبوت سحب الأخبار بصمت في الخلفية
    fetch_automated_news()
    
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
    
    # سحب أحدث الأخبار من قاعدة البيانات لعرضها في البوابة
    news = TradingNews.query.filter_by(is_visible=True).order_by(TradingNews.created_at.desc()).limit(10).all()

    return render_template('trading/trading_portal.html', articles=trading_articles, products=mql_products, brokers=broker_ads, news=news)

@trading_bp.route('/trading_article/<int:id>')
@trading_bp.route('/<lang>/trading_article/<int:id>')
def trading_article_details(id, lang='ar'):
    article = TradingArticle.query.get_or_404(id)
    update_trading_view(trading_article_id=id)
    article.display_title = article.title_en if lang == 'en' and article.title_en else article.title
    article.display_content = article.content_en if lang == 'en' and article.content_en else article.content
    return render_template('trading/trading_article_details.html', article=article)

@trading_bp.route('/mql_product/<int:id>/click')
def mql_product_click(id):
    product = MqlProduct.query.get_or_404(id)
    update_trading_view(mql_product_id=id)
    return redirect(product.mql_url)

@trading_bp.route('/like_trading_article/<int:id>', methods=['POST'])
def like_trading_article(id):
    article = TradingArticle.query.get_or_404(id)
    article.likes = (article.likes or 0) + 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': article.likes})

@trading_bp.route('/news/<int:id>')
@trading_bp.route('/<lang>/news/<int:id>')
def news_details(id, lang='ar'):
    news_item = TradingNews.query.get_or_404(id)
    
    # تحديث مشاهدات الأخبار مباشرة
    news_item.views = (news_item.views or 0) + 1
    db.session.commit()
    
    news_item.display_title = news_item.title_en if lang == 'en' and news_item.title_en else news_item.title
    news_item.display_content = news_item.content_en if lang == 'en' and news_item.content_en else news_item.content
    return render_template('trading/news_details.html', news=news_item)

@trading_bp.route('/live-chart')
@trading_bp.route('/<lang>/live-chart')
def live_chart(lang='ar'):
    return render_template('trading/live_chart.html')