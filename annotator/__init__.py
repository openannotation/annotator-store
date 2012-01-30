"""
Backend for web annotation.

@copyright: (c) 2006-2012 Open Knowledge Foundation
"""
__version__ = '0.5.1'
__license__ = 'MIT'
__author__ = 'Rufus Pollock and Nick Stenning (Open Knowledge Foundation)'

__all__ = ['__version__', '__license__', '__author__',
           'app', 'db', 'es', 'create_all', 'drop_all']

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

def create_indices():
    from . import model
    es.create_index(model.annotation.INDEX)
    es.put_mapping(model.annotation.TYPE,
                   {'properties': model.annotation.MAPPING},
                   model.annotation.INDEX)

def drop_indices():
    es.delete_index(model.annotation.INDEX)

def create_all():
    # This import must remain here to prevent circular imports from annotator.model
    from . import model
    db.create_all()
    create_indices()

def drop_all():
    from . import model
    db.drop_all()
    drop_indices()
