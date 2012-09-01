from nose.tools import *
from mock import MagicMock, patch

import pyes

from annotator.elasticsearch import ElasticSearch, _Model

class TestElasticSearch(object):

    def test_init_without_app(self):
        es = ElasticSearch()
        assert_equal(es.app, None)

    def test_init_with_app(self):
        app = MagicMock()
        es = ElasticSearch(app)
        assert_equal(es.app, app)

    def test_init_creates_model(self):
        es = ElasticSearch()
        assert_equal(es.Model.mro()[1], _Model)

    def test_init_app(self):
        app = MagicMock()
        es = ElasticSearch()
        es.init_app(app)
        assert_equal(es.app, None)

    def test_adds_to_app_extensions(self):
        class App(object):
            name = 'foo'
            config = MagicMock()
        app = App()
        es = ElasticSearch(app)
        assert_equal(app.extensions['elasticsearch'], es)

    def test_noapp_error(self):
        es = ElasticSearch()
        assert_raises(RuntimeError, es.get_app)

    def test_index(self):
        app = MagicMock()
        app.config.__getitem__.return_value = 'foobar'
        es = ElasticSearch(app)
        assert_equal(es.index, 'foobar')

    @patch('annotator.elasticsearch.pyes.ES')
    def test_conn(self, pyes_mock):
        app = MagicMock()
        es = ElasticSearch(app)
        assert_equal(es.conn, pyes_mock.return_value)

class TestModel(object):
    def setup(self):
        self.app = MagicMock()
        self.es = ElasticSearch(self.app)

        class MyModel(self.es.Model):
            __type__ = 'footype'

        self.Model = MyModel

    @patch('annotator.elasticsearch.pyes.ES')
    def test_fetch(self, pyes_mock):
        conn = pyes_mock.return_value
        conn.get.return_value = {'foo': 'bar'}
        o = self.Model.fetch(123)
        assert_equal(o['foo'], 'bar')
        assert_equal(o['id'], 123)
        assert_true(isinstance(o, self.Model))

    @patch('annotator.elasticsearch.pyes.ES')
    def test_fetch_not_found(self, pyes_mock):
        conn = pyes_mock.return_value
        def raise_exc(self, *args, **kwargs):
            raise pyes.exceptions.NotFoundException('foo')
        conn.get.side_effect = raise_exc
        o = self.Model.fetch(123)
        assert_equal(o, None)
