from datetime import datetime

from flask import Module, redirect, request, url_for, render_template, session
from flask import flash
from flaskext.wtf import *
from werkzeug import generate_password_hash, check_password_hash

account = Module(__name__)

from flask import current_app 
from .model import Account


@account.route('/')
def index():
    return 'Accounts home page'

class login_form(Form):
    username = TextField('Username', [validators.Required()])
    password = TextField('Password', [validators.Required()])

@account.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    # return render_template('login.html', error=error)
    return 'Login!'

@account.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('.home'))


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
        flash('Thanks for signing-up')
        return redirect(url_for('login'))
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors')
    return render_template('account/signup.html', form=form)

