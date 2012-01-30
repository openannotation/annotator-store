from .. import helpers as h

from annotator import db
from annotator.model.consumer import *

def save(c):
    db.session.add(c)
    db.session.flush()

class TestConsumer(object):

    def setup(self):
        db.create_all()

    def teardown(self):
        db.session.close()
        db.drop_all()

    def test_key(self):
        c = Consumer(key='foo')
        save(c)

        c = Consumer.fetch('foo')
        h.assert_equal(c.key, 'foo')

    def test_secret(self):
        c = Consumer(key='foo')
        save(c)

        assert c.secret, 'Consumer secret should be set!'
