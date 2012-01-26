import os
from flask import Flask, render_template, session, g
from store import store
from .account import account

app = Flask('annotator')


def setup_app():
    configure_app()
    app.register_module(store, url_prefix=app.config.get('MOUNTPOINT', ''))
    app.register_module(account, url_prefix='/account')

    sqlalchemy_db = app.config.get('DB', '')
    if sqlalchemy_db:
        import annotator.model.sqlelixir as model
        model.metadata.bind = app.config['DB']
        # Create tables
        model.setup_all(True)
    couchdb = app.config.get('COUCHDB_DATABASE', '')
    if couchdb:
        import annotator.model.couch as model
        model.init_model(app.config)


def configure_app():
    '''Configure app loading in order from:

    [annotator.settings_default]
    [annotator.settings_local]
    annotator.cfg # in app root dir
    config file specified by env var ANNOTATOR_CONFIG
    '''
    # app.config.from_object('annotator.settings_default')
    # app.config.from_object('annotator.settings_local')
    here = os.path.dirname(os.path.abspath( __file__ ))
    # parent directory
    config_path = os.path.join(os.path.dirname(here), 'annotator.cfg')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)
    if 'ANNOTATOR_CONFIG' in os.environ:
        app.config.from_envvar('ANNOTATOR_CONFIG')
    ADMINS = app.config.get('ADMINS', '')
    if not app.debug and ADMINS:
        import logging
        from logging.handlers import SMTPHandler
        mail_handler = SMTPHandler('127.0.0.1',
                                   'server-error@no-reply.com',
                                   ADMINS, 'annotator error')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


@app.before_request
def before_request():
    g.account_id = session.get('account-id', None)

@app.route('/')
def home():
    return render_template('index.html')

