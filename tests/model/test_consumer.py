from .. import TestCase, helpers as h

from annotator.model import Consumer

class TestConsumer(TestCase):

    def test_key(self):
        c = Consumer(key='foo')
        h.db_save(c)

        c = Consumer.fetch('foo')
        h.assert_equal(c.key, 'foo')

    def test_secret(self):
        c = Consumer(key='foo')
        h.db_save(c)

        assert c.secret, 'Consumer secret should be set!'
