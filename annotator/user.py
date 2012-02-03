import httplib
import urllib

from flask import Blueprint, current_app
from flask import g, redirect, request, url_for, render_template, session, flash
from flaskext.wtf import *

import sqlalchemy

from annotator import db
from annotator.model import User, Annotation

user = Blueprint('user', __name__)

def get_current_user():
    username = session.get('user')
    if not username:
        return None
    else:
        return User.query.filter_by(username=username).first()

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
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user'] = user.username
            flash('Welcome back', 'success')
            return redirect(url_for('.home'))

        else:
            flash('Email/password combination not recognized', 'error')

    if request.method == 'POST' and not form.validate():
        flash('Invalid form', 'error')

    return render_template('user/login.html', form=form)


@user.route('/logout')
def logout():
    session.pop('user', None)
    flash('You were logged out')

    return redirect(url_for('.login'))

@user.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate() and _add_user(form):
        flash('Thank you for signing up!', 'success')
        return redirect(url_for('.login'))
    else:
        flash('Errors found while attempting to sign up!')
        return render_template('user/signup.html', form=form)

@user.route('/home')
def home():
    if not g.user:
        flash('Please log in to see your profile!')
        return redirect(url_for('.login'))

    store_api = 'http://' + request.headers.get('host') + current_app.config.get('MOUNTPOINT', '')

    bookmarklet = _get_bookmarklet(g.user, store_api)
    annotations = Annotation.search(user=g.user.username, limit=20)

    return render_template('user/home.html',
                           user=g.user,
                           bookmarklet=bookmarklet,
                           annotations=annotations)

def _add_user(form):
    user = User(username=form.username.data,
                email=form.email.data,
                password=form.password.data)
    db.session.add(user)

    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        if 'email is not unique' in e.message:
            form.email.errors.append("This email address is already registered: please use another.")
        if 'username is not unique' in e.message:
            form.username.errors.append("This username is taken: please use another.")
        return False

    # Fallthrough: all's gone well.
    return True

def _get_bookmarklet(user, store_api):
    config = render_template('user/bookmarklet.config.json',
                             user=user,
                             store_api=store_api)

    bookmarklet = render_template('user/bookmarklet.js', config=config)
    bookmarklet = _compress(bookmarklet)

    return bookmarklet

def _compress(javascript):
    '''Compress bookmarklet using closure compiler.'''

    if current_app.config['DEBUG']:
        return javascript

    params = urllib.urlencode([
        ('js_code', javascript),
        ('compilation_level', 'WHITESPACE_ONLY'),
        ('output_format', 'text'),
        ('output_info', 'compiled_code'),
    ])

    headers = { "Content-Type": "application/x-www-form-urlencoded" }
    conn = httplib.HTTPConnection('closure-compiler.appspot.com')
    conn.request('POST', '/compile', params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close
    return data

