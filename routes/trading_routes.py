from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from core.models import TradingArticle, MqlProduct, BrokerAd, ViewTracker, db
import hashlib
from datetime import datetime, timedelta, date

trading_bp = Blueprint('trading', __name__)

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

@trading_bp.route('/trading')
@trading_bp.route('/<lang>/trading')
def trading_portal(lang='ar'):
    if lang not in ['ar', 'en']: return redirect(url_for('trading.trading_portal'))
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

    return render_template('trading/trading_portal.html', articles=trading_articles, products=mql_products, brokers=broker_ads) # المسار المحدث

@trading_bp.route('/trading_article/<int:id>')
@trading_bp.route('/<lang>/trading_article/<int:id>')
def trading_article_details(id, lang='ar'):
    article = TradingArticle.query.get_or_404(id)
    update_trading_view(trading_article_id=id)
    article.display_title = article.title_en if lang == 'en' and article.title_en else article.title
    article.display_content = article.content_en if lang == 'en' and article.content_en else article.content
    return render_template('trading/trading_article_details.html', article=article) # المسار المحدث

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