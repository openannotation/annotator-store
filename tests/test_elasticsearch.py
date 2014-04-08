from nose.tools import *
from mock import MagicMock, patch
from flask import Flask

import elasticsearch

from annotator.elasticsearch import ElasticSearch, _Model

class TestElasticSearch(object):

    def test_noapp_error(self):
        es = ElasticSearch()
        assert_raises(RuntimeError, lambda: es.conn)

    def test_conn(self):
        app = Flask('testy')
        app.config['ELASTICSEARCH_HOST'] = 'http://127.0.1.1:9202'
        app.config['ELASTICSEARCH_INDEX'] = 'foobar'
        es = ElasticSearch(app)
        with app.app_context():
            assert_true(isinstance(es.conn, elasticsearch.Elasticsearch))

    def test_auth(self):
        app = Flask('testy')
        app.config['ELASTICSEARCH_HOST'] = 'http://foo:bar@127.0.1.1:9202'
        app.config['ELASTICSEARCH_INDEX'] = 'foobar'
        es = ElasticSearch(app)
        with app.app_context():
            assert_equal(('foo', 'bar'),
                         es.conn.transport.hosts[0]['http_auth'])

    def test_index(self):
        app = Flask('testy')
        app.config['ELASTICSEARCH_INDEX'] = 'foobar'
        es = ElasticSearch(app)
        with app.app_context():
            assert_equal(es.index, 'foobar')

class TestModel(object):
    def setup(self):
        app = Flask('testy')
        app.config['ELASTICSEARCH_HOST'] = 'http://127.0.1.1:9202'
        app.config['ELASTICSEARCH_INDEX'] = 'foobar'
        self.es = ElasticSearch(app)

        class MyModel(self.es.Model):
            __type__ = 'footype'

        self.Model = MyModel

        self.ctx = app.app_context()
        self.ctx.push()

    def teardown(self):
        self.ctx.pop()

    @patch('annotator.elasticsearch.elasticsearch.Elasticsearch')
    def test_fetch(self, es_mock):
        conn = es_mock.return_value
        conn.get.return_value = {'_source': {'foo': 'bar'}}
        o = self.Model.fetch(123)
        assert_equal(o['foo'], 'bar')
        assert_equal(o['id'], 123)
        assert_true(isinstance(o, self.Model))

    @patch('annotator.elasticsearch.elasticsearch.Elasticsearch')
    def test_fetch_not_found(self, es_mock):
        conn = es_mock.return_value
        def raise_exc(*args, **kwargs):
            raise elasticsearch.exceptions.NotFoundError('foo')
        conn.get.side_effect = raise_exc
        o = self.Model.fetch(123)
        assert_equal(o, None)
