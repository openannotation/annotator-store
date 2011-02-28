from datetime import datetime

from flask import Module, redirect, request, url_for, render_template, session
from flask import flash
# from flaskext.wtf import *
from werkzeug import generate_password_hash, check_password_hash

account = Module(__name__)

from flask import current_app 
from .model import Account


'''
class signup_form(Form):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', [validators.Required()])
    email = TextField('eMail', [validators.Required()])

class login_form(Form):
    username = TextField('Username', [validators.Required()])
    password = TextField('Password', [validators.Required()])
'''

@account.route('/')
def index():
    return 'Accounts home page'

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

@account.route('/signup')
def signup():
    return 'Signup form coming soon!'

