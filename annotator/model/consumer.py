from datetime import datetime
import uuid

from annotator import db

__all__ = ['Consumer']

def _uuid():
    return str(uuid.uuid4())

class Consumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True)
    secret = db.Column(db.String(36), default=_uuid)
    ttl = db.Column(db.Integer, default=86400)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @classmethod
    def fetch(cls, key):
        return cls.query.filter_by(key=key).first()

    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return '<Consumer %r>' % self.key


