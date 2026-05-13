from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from deep_translator import GoogleTranslator

# إنشاء كائن قاعدة البيانات
db = SQLAlchemy()

# كائن المترجم
translator = GoogleTranslator(source='ar', target='en')

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = 'al_mustafa_secure_2026_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../portfolio.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # ربط قاعدة البيانات بالتطبيق
    db.init_app(app)

    return app