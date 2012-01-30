from .. import helpers as h

from annotator import db
from annotator.model.user import *

def save(x):
    db.session.add(x)
    db.session.flush()

class TestConsumer(object):

    def setup(self):
        db.create_all()

    def teardown(self):
        db.session.close()
        db.drop_all()

    def test_constructor(self):
        u = User('joe', 'joe@bloggs.com')
        h.assert_equal(u.username, 'joe')
        h.assert_equal(u.email, 'joe@bloggs.com')
