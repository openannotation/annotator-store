from datetime import datetime
import hashlib

from flask import Module, redirect, request, url_for, render_template, session
from flask import flash, g, abort
from flaskext.wtf import *
from werkzeug import generate_password_hash, check_password_hash

account = Module(__name__)

from flask import current_app 
from .model import Account

@account.before_request
def before_request():
    g.account_id = session.get('account-id', None) 


@account.route('/')
def index():
    return 'Accounts home page'


class LoginForm(Form):
    email = TextField('Email', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

@account.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        email = form.email.data
        accounts = Account.get_by_email(email)
        if accounts and check_password_hash(accounts[0].pwdhash, password):
            acc = accounts[0]
            session['account-id'] = acc.id
            flash('Welcome back', 'success')
            return redirect(url_for('view', id=acc.id))
        else:
            flash('Incorrect email/password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid form')
    return render_template('account/login.html', form=form)


@account.route('/logout')
def logout():
    session.pop('account-id', None)
    flash('You were logged out')
    return redirect(url_for('.home'))


@account.route('/v/<id>')
def view(id):
    if g.account_id != id:
        return abort(401)
    acc = Account.get(g.account_id)
    token = hashlib.sha256(acc.secret + acc.username).hexdigest()
    account = Account.get(id)
    return render_template('account/view.html', account=account, token=token)


class SignupForm(Form):
    username = TextField('Username', [validators.Length(min=3, max=25)])
    email = TextField('Email Address', [validators.Length(min=3, max=35)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

@account.route('/signup', methods=['GET', 'POST'])
def signup():
    # TODO: re-enable csrf
    form = SignupForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        pwdhash = generate_password_hash(form.password.data)
        account = Account(username=form.username.data, email=form.email.data,
                    pwdhash=pwdhash)
        account.save()
        flash('Thanks for signing-up', 'success')
        return redirect(url_for('login'))
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors')
    return render_template('account/signup.html', form=form)

