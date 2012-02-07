from .. import TestCase, helpers as h

import annotator
from annotator.model import Consumer

def save(c):
    annotator.db.session.add(c)
    annotator.db.session.commit()

class TestConsumer(TestCase):

    def test_key(self):
        c = Consumer(key='foo')
        save(c)

        c = Consumer.fetch('foo')
        h.assert_equal(c.key, 'foo')

    def test_secret(self):
        c = Consumer(key='foo')
        save(c)

        assert c.secret, 'Consumer secret should be set!'
