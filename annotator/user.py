import httplib
import urllib

from flask import Blueprint, current_app
from flask import g, redirect, request, url_for, render_template, session, flash
from flaskext.wtf import Form, fields as f, validators as v, html5

import sqlalchemy

from annotator import db
from annotator.model import User, Consumer, Annotation

user = Blueprint('user', __name__)

def get_current_user():
    username = session.get('user')
    if not username:
        return None
    else:
        return User.query.filter_by(username=username).first()

## WTForms classes

class LoginForm(Form):
    login    = f.TextField('Username/email', [v.Required()])
    password = f.PasswordField('Password',   [v.Required()])

class SignupForm(Form):
    username = f.TextField('Username', [
        v.Length(min=3, max=128),
        v.Regexp(r'^[^@]*$', message="Username shouldn't be an email address")
    ])
    email = html5.EmailField('Email address', [
        v.Length(min=3, max=128),
        v.Email(message="This should be a valid email address.")
    ])
    password = f.PasswordField('Password', [
        v.Required(),
        v.Length(min=8, message="It's probably best if your password is longer than 8 characters."),
        v.EqualTo('confirm', message="Passwords must match.")
    ])
    confirm = f.PasswordField('Confirm password')

    # Will only work if set up in config (see http://packages.python.org/Flask-WTF/)
    captcha = f.RecaptchaField('Captcha')


## Routes

@user.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('.home'))

    form = LoginForm()

    if form.validate_on_submit():
        if '@' in form.login.data:
            user = User.query.filter_by(email=form.login.data).first()
        else:
            user = User.query.filter_by(username=form.login.data).first()

        if user and user.check_password(form.password.data):
            session['user'] = user.username
            flash('Welcome back', 'success')
            return redirect(url_for('.home'))
        else:
            flash('Email/password combination not recognized', 'error')

    return render_template('user/login.html', form=form)


@user.route('/logout')
def logout():
    session.pop('user', None)
    flash('You were logged out')

    return redirect(url_for('.login'))

@user.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit() and _add_user(form):
        flash('Thank you for signing up!', 'success')
        session['user'] = form.username.data
        return redirect(url_for('.home'))

    if request.method == 'POST':
        flash('Errors found while attempting to sign up!')

    captcha = 'RECAPTCHA_PUBLIC_KEY' in current_app.config

    return render_template('user/signup.html', form=form, captcha=captcha)

@user.route('/home')
def home():
    _require_user('to see your profile')

    bookmarklet = render_template('bookmarklet.js', root=current_app.config['ROOT_URL'])
    annotations = Annotation.search(user=g.user.username, limit=20)

    return render_template('user/home.html',
                           user=g.user,
                           bookmarklet=bookmarklet,
                           annotations=annotations)

@user.route('/consumer/add')
def add_consumer():
    _require_user()

    c = Consumer()
    g.user.consumers.append(c)

    db.session.commit()

    return redirect(url_for('.home'))

@user.route('/consumer/delete/<key>')
def delete_consumer(key):
    _require_user()

    c = g.user.consumers.filter_by(key=key).first()

    if not c:
        flash("Couldn't delete consumer '{0}' because I couldn't find it!".format(key), 'error')
    else:
        db.session.delete(c)
        db.session.commit()

    return redirect(url_for('.home'))

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

def _require_user(msg=''):
    if not g.user:
        flash('Please log in{0}'.format(' ' + msg))
        return redirect(url_for('.login'))
