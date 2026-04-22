from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

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
    icon = db.Column(db.String(50), default='fas fa-code')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(25), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

# --- حماية المسارات (Login Decorator) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

with app.app_context():
    db.create_all()

# --- المسارات العامة ---
@app.route('/')
def home():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

@app.route('/project/<int:id>')
def project_details(id):
    project = Project.query.get_or_404(id)
    return render_template('project_details.html', project=project)

@app.route('/contact', methods=['POST'])
def contact():
    new_msg = Message(name=request.form.get('name'), email=request.form.get('email'), 
                      phone=request.form.get('phone'), content=request.form.get('content'))
    db.session.add(new_msg)
    db.session.commit()
    flash("Message sent to Al-Mustafa Programming. We will contact you soon.")
    return redirect(url_for('home'))

# --- نظام تسجيل الدخول ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'mustafa2026':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        flash("Invalid Credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

# --- لوحة التحكم (المحمية) ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        new_project = Project(title=request.form['title'], description=request.form['description'],
                             full_details=request.form['full_details'], technologies=request.form['technologies'],
                             icon=request.form['icon'])
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('admin'))
    
    projects = Project.query.all()
    messages = Message.query.order_by(Message.id.desc()).all()
    unread_count = Message.query.filter_by(is_read=False).count()
    return render_template('admin.html', projects=projects, messages=messages, unread=unread_count)

@app.route('/read/<int:id>')
@login_required
def mark_read(id):
    msg = Message.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
@login_required
def delete_project(id):
    db.session.delete(Project.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)