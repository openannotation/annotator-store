from datetime import datetime
import uuid

from annotator import db

__all__ = ['Consumer']

# The distinction between _uuid and _uuid_hex is, technically, irrelevant.
# We only make a distinction (key=hex, secret=standard form) in order to
# reduce user confusion. That is, if they both looked the same, it would be
# easy to forget which was which. This has security implications, so it's
# best they at least *look* different.

def _uuid():
    return str(uuid.uuid4())

def _uuid_hex():
    return uuid.uuid4().hex

class Consumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, default=_uuid_hex)
    secret = db.Column(db.String(36), default=_uuid)
    ttl = db.Column(db.Integer, default=86400)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @classmethod
    def fetch(cls, key):
        return cls.query.filter_by(key=key).first()

    def __init__(self, key=None):
        self.key = key

    def __repr__(self):
        return '<Consumer %r>' % self.key


