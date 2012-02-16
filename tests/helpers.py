from nose.tools import *
from mock import Mock, patch
from flask import current_app

def db_save(x):
    db = current_app.extensions['sqlalchemy'].db
    db.session.add(x)
    db.session.commit()
