"""
Backend for web annotation.

@copyright: (c) 2006-2012 Open Knowledge Foundation
"""
__version__ = '0.5.1'
__license__ = 'MIT'
__author__ = 'Rufus Pollock and Nick Stenning (Open Knowledge Foundation)'

__all__ = ['__version__', '__license__', '__author__',
           'app', 'db', 'es', 'create_indices', 'drop_indices', 'create_all', 'drop_all']

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy
import pyes

app = Flask(__name__, instance_relative_config=True)

app.config.from_object('annotator.default_settings')
app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'] % app.instance_path

app.config.from_pyfile('annotator.cfg', silent=True)
app.config.from_envvar('ANNOTATOR_CONFIG', silent=True)

# Configure database
db = SQLAlchemy(app)

# Configure ES
es = pyes.ES(app.config['ELASTICSEARCH_HOST'])

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

def create_indices():
    from .model.annotation import INDEX, TYPE, MAPPING
    es.create_index(INDEX)
    es.put_mapping(TYPE, {'properties': MAPPING}, INDEX)

def drop_indices():
    from .model.annotation import INDEX
    es.delete_index(INDEX)

def create_all():
    # This import must remain here to prevent circular imports from annotator.model
    from . import model
    db.create_all()
    create_indices()

def drop_all():
    from . import model
    db.drop_all()
    drop_indices()
