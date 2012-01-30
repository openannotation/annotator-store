from datetime import datetime
from werkzeug import generate_password_hash, check_password_hash

from .. import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(120))

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    consumers = db.relationship('Consumer', backref='user', lazy='dynamic')

    @classmethod
    def fetch(cls, id):
        return cls.query.filter_by(id=id).first()

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

    def _password_set(self, v):
        self.pwdhash = generate_password_hash(v)

    password = property(None, _password_set)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
