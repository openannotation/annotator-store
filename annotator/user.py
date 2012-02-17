import httplib
import urllib

from flask import Blueprint
from flask import current_app, g
from flask import redirect, request, url_for, render_template, session, flash

from flaskext.wtf import Form, fields as f, validators as v, html5
from flaskext.mail import Message

import itsdangerous
import sqlalchemy

from annotator import util
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
        v.Regexp(r'^[^@:]*$', message="Username shouldn't contain '@' or ':'")
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

class ResetPasswordRequestForm(Form):
    login = f.TextField('Username/email', [v.Required()])

class ResetPasswordForm(Form):
    password = f.PasswordField('New password', [
        v.Required(),
        v.Length(min=8, message="It's probably best if your password is longer than 8 characters."),
        v.EqualTo('confirm', message="Passwords must match.")
    ])
    confirm = f.PasswordField('Confirm password')

## Routes

@user.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('.home'))

    form = LoginForm()

    if form.validate_on_submit():
        user = _get_user(form.login.data)

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
@util.require_user
def home():
    bookmarklet = render_template('bookmarklet.js', root=current_app.config['ROOT_URL'])
    annotations = Annotation.search(user=g.user.username, limit=20)

    return render_template('user/home.html',
                           user=g.user,
                           bookmarklet=bookmarklet,
                           annotations=annotations)

@user.route('/consumer/add')
@util.require_user
def add_consumer():
    c = Consumer()
    g.user.consumers.append(c)

    db.session.commit()

    return redirect(url_for('.home'))

@user.route('/consumer/delete/<key>')
@util.require_user
def delete_consumer(key):
    c = g.user.consumers.filter_by(key=key).first()

    if not c:
        flash("Couldn't delete consumer '{0}' because I couldn't find it!".format(key), 'error')
    else:
        g.db.session.delete(c)
        g.db.session.commit()

    return redirect(url_for('.home'))

@user.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if g.user:
        flash('Already logged in. You can change your password here!')
        return redirect(url_for('.home'))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = _get_user(form.login.data)

        if user:
            _send_reset_password_email(user)
            flash('Please check your email for a link to reset your password!', 'success')
            return redirect(url_for('.login'))
        else:
            flash('Username/email not found in our database!')


    return render_template('user/reset_password_request.html', form=form)


@user.route('/reset_password/<code>', methods=['GET', 'POST'])
def reset_password(code):
    try:
        username = _check_reset_password_code(code)
    except itsdangerous.SignatureExpired:
        flash('Reset code expired, please get another one!', 'error')
        return redirect(url_for('.reset_password_request'))
    except itsdangerous.BadSignature:
        flash('Could not verify reset code. Please try again!', 'error')
        return redirect(url_for('.reset_password_request'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()

        if user:
            user.password = form.password.data
            g.db.session.commit()
            flash('Password successfully reset: please log in.', 'success')
        else:
            flash('Username not found in our database!', 'error')

        return redirect(url_for('.login'))

    return render_template('user/reset_password.html', form=form)

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

def _get_user(email_or_username):
    if '@' in email_or_username:
        user = User.query.filter_by(email=email_or_username).first()
    else:
        user = User.query.filter_by(username=email_or_username).first()
    return user

def _send_reset_password_email(user):
    code = _generate_reset_password_code(user)
    body = render_template('user/reset_password_email.txt', code=code, user=user)

    msg = Message("Reset password", recipients=[user.email])
    msg.body = body

    g.mail.send(msg)

def _generate_reset_password_code(user):
    u = itsdangerous.URLSafeTimedSerializer(current_app.secret_key, salt='reset_password')
    return u.dumps(user.username)

def _check_reset_password_code(code):
    u = itsdangerous.URLSafeTimedSerializer(current_app.secret_key, salt='reset_password')
    return u.loads(code, max_age=7200)
