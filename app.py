import secrets

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('passwords', lazy=True))

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

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Benutzername bereits vergeben!")

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return render_template('login.html', error="Ungültiger Benutzername oder Passwort!")

        session['user_id'] = user.id
        session['username'] = user.username

        return redirect(url_for('vault'))

    return render_template('login.html', error=None)


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

        current_user = User.query.get(session['user_id'])

        if not current_user:
            return render_template('add_account_details.html', error="Benutzer nicht gefunden!")

        new_account = Account(site=site, username=username, password=password, user_id=current_user.id)
        db.session.add(new_account)
        db.session.commit()
        print("test")

        return redirect(url_for('vault'))

    return render_template('add_account_details.html')


@app.route('/vault')
def vault():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user_accounts = Account.query.filter_by(user_id=user.id).all()

    print("Vault aufgerufen von User ID:", session.get('user_id'))
    print("Anzahl Accounts gefunden:", len(user_accounts))

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

        db.session.commit()

        return redirect(url_for('vault'))

    return render_template('edit_account_details.html', site=account_to_edit.site, username=account_to_edit.username, password=account_to_edit.password)

@app.route('/delete_account_details/<int:id>', methods=['GET', 'POST'])
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