"""
Backend for web annotation.

@copyright: (c) 2006-2012 Open Knowledge Foundation
"""
__version__ = '0.6'
__license__ = 'MIT'
__author__ = 'Rufus Pollock and Nick Stenning (Open Knowledge Foundation)'

__all__ = ['__version__', '__license__', '__author__',
           'create_app', 'create_db', 'drop_db',
           'create_indices', 'drop_indices',
           'create_all', 'drop_all']

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy
import pyes

app = None
db = SQLAlchemy()
es = None

def create_app():
    global app, db, es

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('annotator.default_settings')
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'] % app.instance_path

    app.config.from_pyfile('annotator.cfg', silent=True)
    app.config.from_envvar('ANNOTATOR_CONFIG', silent=True)

    # Configure database
    db.init_app(app)

    # Configure ES
    from . import model
    es = pyes.ES(app.config['ELASTICSEARCH_HOST'])
    model.annotation.configure(es, app.config)

    # Mount controllers
    from .store import store
    from .user import user
    from .home import home

    if app.config['MOUNT_STORE']:
        app.register_blueprint(store, url_prefix=app.config['MOUNT_STORE'])
    if app.config['MOUNT_USER']:
        app.register_blueprint(user, url_prefix=app.config['MOUNT_USER'])
    if app.config['MOUNT_HOME']:
        app.register_blueprint(home, url_prefix=app.config['MOUNT_HOME'])

    return app

def create_indices():
    with app.test_request_context():
        from .model.annotation import index, TYPE, MAPPING
        es.create_index(index)
        es.put_mapping(TYPE, {'properties': MAPPING}, index)

def drop_indices():
    with app.test_request_context():
        from .model.annotation import index
        es.delete_index(index)

def create_db():
    from . import model
    with app.test_request_context():
        db.create_all()

def drop_db():
    from . import model
    with app.test_request_context():
        db.drop_all()

def create_all():
    create_indices()
    create_db()

def drop_all():
    drop_indices()
    drop_db()
