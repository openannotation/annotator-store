from datetime import datetime
import hashlib

from flask import Module, redirect, request, url_for, render_template, session
from flask import flash, g, abort
from flaskext.wtf import *

account = Module(__name__)

from flask import current_app
from .model import Account, Annotation

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
        if accounts and accounts[0].check_password(password):
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
    store_api = 'http://' + request.headers.get('host') + current_app.config.get('MOUNTPOINT', '')
    bookmarklet = get_bookmarklet(account, token, store_api)
    annotations = list(Annotation.search(account_id=id, limit=20))
    return render_template('account/view.html',
        account=account,
        token=token,
        bookmarklet=bookmarklet,
        annotations=annotations
        )


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
        account = Account(username=form.username.data, email=form.email.data)
        account.password = form.password.data
        account.save()
        flash('Thanks for signing-up', 'success')
        return redirect(url_for('login'))
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors')
    return render_template('account/signup.html', form=form)


#######################################
## Helper methods

def get_bookmarklet(account, token, store_api):
    config = render_template('account/bookmarklet.config.json',
            account=account, token=token, store_api=store_api)
    bookmarklet = render_template('account/bookmarklet.js', config=config)
    bookmarklet = compress(bookmarklet)
    return bookmarklet


import httplib, urllib
def compress(javascript):
    '''Compress bookmarklet using closure compiler.'''
    params = urllib.urlencode([
            ('js_code', javascript),
            ('compilation_level', 'WHITESPACE_ONLY'),
            ('output_format', 'text'),
            ('output_info', 'compiled_code'),
        ])

    # Always use the following value for the Content-type header.
    headers = { "Content-type": "application/x-www-form-urlencoded" }
    conn = httplib.HTTPConnection('closure-compiler.appspot.com')
    conn.request('POST', '/compile', params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close
    return data

