import os
from flask import Flask, render_template
from store import store
import model


app = Flask('annotator')


def setup_app():
    configure_app()
    app.register_module(store, url_prefix=app.config.get('MOUNTPOINT', ''))

    model.metadata.bind = app.config['DB']
    # Create tables
    model.setup_all(True)
    # For testing purposes only
    if app.config.get('TEST_CONSUMER', ''):
        from annotator.test_consumer import consumer
        consumer.test_consumer_key  = app.config['TEST_CONSUMER_KEY']
        consumer.test_consumer_user = app.config['TEST_CONSUMER_USER']
        store.app.register_module(consumer, url_prefix='/auth')


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

@app.route('/')
def home():
    return render_template('index.html')

