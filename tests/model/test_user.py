from .. import helpers as h

from annotator import db
from annotator.model.user import *

def save(x):
    db.session.add(x)
    db.session.commit()

class TestUser(object):

    def setup(self):
        db.create_all()

    def teardown(self):
        db.drop_all()

    def test_constructor(self):
        u = User('joe', 'joe@bloggs.com')
        h.assert_equal(u.username, 'joe')
        h.assert_equal(u.email, 'joe@bloggs.com')

    def test_password(self):
        u = User('joe', 'joe@bloggs.com')
        u.password = 'foo'
        h.assert_is_not_none(u.password_hash)
        h.assert_true(u.check_password('foo'))

    def test_null_password(self):
        u = User('joe', 'joe@bloggs.com')
        h.assert_false(u.check_password('foo'))
