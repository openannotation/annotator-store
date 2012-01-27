from datetime import datetime
import hashlib
import httplib
import urllib

from flask import Module, redirect, request, url_for, render_template, session
from flask import flash, g, abort
from flaskext.wtf import *

user = Module(__name__)

from flask import current_app
from .model import User, Annotation

## WTForms classes

class LoginForm(Form):
    email = TextField('Email', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

class SignupForm(Form):
    username = TextField('Username', [validators.Length(min=3, max=25)])
    email = TextField('Email Address', [validators.Length(min=3, max=35)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

## Routes

@user.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        email = form.email.data
        users = User.get_by_email(email)
        if users and users[0].check_password(password):
            u = users[0]
            session['user_id'] = u.id
            flash('Welcome back', 'success')
            return redirect(url_for('view', id=u.id))
        else:
            flash('Incorrect email/password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid form')
    return render_template('user/login.html', form=form)


@user.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You were logged out')
    return redirect(url_for('.home'))

@user.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        user.save()

        flash('Thanks for signing up!', 'success')
        return redirect(url_for('login'))

    if request.method == 'POST' and not form.validate():
        flash('Errors found while attempting to sign up!')

    return render_template('user/signup.html', form=form)

@user.route('/<id>')
def view(id):
    user_id = session.get('user_id')

    if not user_id == id:
        return abort(401)

    u = User.get(user_id)

    store_api = 'http://' + request.headers.get('host') + current_app.config.get('MOUNTPOINT', '')

    bookmarklet = _get_bookmarklet(user, store_api)
    annotations = list(Annotation.search(user_id=user_id, limit=20))

    return render_template('user/view.html',
                           user=user,
                           bookmarklet=bookmarklet,
                           annotations=annotations)


def _get_bookmarklet(user, store_api):
    config = render_template('user/bookmarklet.config.json',
                             user=user,
                             store_api=store_api)

    bookmarklet = render_template('user/bookmarklet.js', config=config)
    bookmarklet = _compress(bookmarklet)

    return bookmarklet

def _compress(javascript):
    '''Compress bookmarklet using closure compiler.'''
    params = urllib.urlencode([
        ('js_code', javascript),
        ('compilation_level', 'WHITESPACE_ONLY'),
        ('output_format', 'text'),
        ('output_info', 'compiled_code'),
    ])

    # Always use the following value for the Content-Type header.
    headers = { "Content-Type": "application/x-www-form-urlencoded" }
    conn = httplib.HTTPConnection('closure-compiler.appspot.com')
    conn.request('POST', '/compile', params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close
    return data

