from .. import TestCase, helpers as h

from annotator.model import User

class TestUser(TestCase):

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
