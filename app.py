import secrets

from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'nightlp777@gmail.com'
app.config['MAIL_PASSWORD'] = 'hcfivkmnaagtrago'
app.config['MAIL_DEFAULT_SENDER'] = 'accounttresor'

mail = Mail(app)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(app.secret_key)
        return s.dumps(self.id, salt='password-reset')

    @staticmethod
    def verify_reset_token(token):
        s = URLSafeTimedSerializer(app.secret_key)
        try:
            user_id = s.loads(token, salt='password-reset', max_age=1800)
        except:
            return None
        return User.query.get(user_id)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('passwords', lazy=True))
    email = db.Column(db.String(120), nullable=False)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('vault'))

    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Benutzername oder E-Mail bereits vergeben!")

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        login_input = request.form['username']
        password = request.form['password']

        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()
        if not user or not check_password_hash(user.password, password):
            return render_template('login.html', error="Ungültiger Benutzername/E-Mail oder Passwort!")

        session['user_id'] = user.id
        session['username'] = user.username

        return redirect(url_for('vault'))

    return render_template('login.html', error=None)

@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for('reset_token', token=token, _external=True)
            msg = Message('Passwort zurücksetzen',
                          recipients=[user.email])
            msg.body = f'''Hallo {user.username},

Du hast eine Zurücksetzung deines Passworts angefordert.

Klicke auf den folgenden Link, um ein neues Passwort zu setzen:

{reset_url}

Wenn du das nicht warst, ignoriere diese E-Mail.

Viele Grüße,
Dein Account Tresor
'''
            mail.send(msg)
            return render_template('reset_request.html', message="E-Mail zum Zurücksetzen wurde gesendet.")
        else:
            return render_template('reset_request.html', error="E-Mail nicht gefunden.")

    return render_template('reset_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if not user:
        return "Link ist ungültig oder abgelaufen."

    if request.method == 'POST':
        password = request.form['password']
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        user.password = hashed_pw
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/add_account_details', methods=['GET', 'POST'])
def add_account_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        site = request.form['site']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        current_user = User.query.get(session['user_id'])

        if not current_user:
            return render_template('add_account_details.html', error="Benutzer nicht gefunden!")

        new_account = Account(site=site, username=username, password=password, email=email, user_id=current_user.id)
        db.session.add(new_account)
        db.session.commit()

        return redirect(url_for('vault'))

    return render_template('add_account_details.html')


@app.route('/vault')
def vault():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user_accounts = Account.query.filter_by(user_id=user.id).all()

    return render_template('vault.html', user_accounts=user_accounts)


@app.route('/edit_account_details/<int:id>', methods=['GET', 'POST'])
def edit_account_details(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    account_to_edit = Account.query.get_or_404(id)

    if account_to_edit.user_id != session['user_id']:
        return redirect(url_for('vault'))

    if request.method == 'POST':
        account_to_edit.site = request.form['site']
        account_to_edit.username = request.form['username']
        account_to_edit.password = request.form['password']
        account_to_edit.email = request.form['email']

        db.session.commit()

        return redirect(url_for('vault'))

    return render_template('edit_account_details.html', site=account_to_edit.site, username=account_to_edit.username, password=account_to_edit.password, email=account_to_edit.email)

@app.route('/delete_account_details/<int:id>', methods=['POST', 'GET'])
def delete_account_details(id):
    if 'user_id' not in session:
        return redirect('/login')

    acc = Account.query.get_or_404(id)

    db.session.delete(acc)
    db.session.commit()
    return redirect('/vault')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)