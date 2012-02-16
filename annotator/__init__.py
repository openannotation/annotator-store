"""
Backend for web annotation.

@copyright: (c) 2006-2012 Open Knowledge Foundation
"""

__all__ = ['__version__', '__license__', '__author__',
           'create_app', 'create_db', 'drop_db',
           'create_indices', 'drop_indices',
           'create_all', 'drop_all']

from flask import Flask, g, current_app
from flaskext.sqlalchemy import SQLAlchemy
import pyes

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('annotator.default_settings')
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'] % app.instance_path

    app.config.from_pyfile('annotator.cfg', silent=True)
    app.config.from_envvar('ANNOTATOR_CONFIG', silent=True)

    # Configure database
    db.init_app(app)

    # Configure ES
    from . import model
    app.extensions['pyes'] = pyes.ES(app.config['ELASTICSEARCH_HOST'])

    # Mount controllers
    from annotator import store, user, home

    if app.config['MOUNT_STORE']:
        app.register_blueprint(store.store, url_prefix=app.config['MOUNT_STORE'])
    if app.config['MOUNT_USER']:
        app.register_blueprint(user.user, url_prefix=app.config['MOUNT_USER'])
    if app.config['MOUNT_HOME']:
        app.register_blueprint(home.home, url_prefix=app.config['MOUNT_HOME'])

    @app.before_request
    def before_request():
        g.db = current_app.extensions['sqlalchemy'].db
        g.es = current_app.extensions['pyes']
        g.user = user.get_current_user()

    return app

def create_indices(app):
    es = app.extensions['pyes']
    index = app.config['ELASTICSEARCH_INDEX']

    with app.test_request_context():
        from .model.annotation import TYPE, MAPPING
        es.create_index(index)
        es.put_mapping(TYPE, {'properties': MAPPING}, index)

def drop_indices(app):
    es = app.extensions['pyes']
    index = app.config['ELASTICSEARCH_INDEX']

    with app.test_request_context():
        es.delete_index(index)

def create_db(app):
    from . import model
    with app.test_request_context():
        db.create_all()

def drop_db(app):
    from . import model
    with app.test_request_context():
        db.drop_all()

def create_all(app):
    create_indices(app)
    create_db(app)

def drop_all(app):
    drop_indices(app)
    drop_db(app)
