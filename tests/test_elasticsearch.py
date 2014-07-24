from nose.tools import *
from mock import MagicMock, patch

import elasticsearch

from annotator.elasticsearch import ElasticSearch, _Model

class TestElasticSearch(object):

    def test_conn(self):
        es = ElasticSearch()
        es.host = 'http://127.0.1.1:9202'
        es.index = 'foobar'
        assert_true(isinstance(es.conn, elasticsearch.Elasticsearch))

    def test_auth(self):
        es = ElasticSearch()
        es.host = 'http://foo:bar@127.0.1.1:9202'
        es.index = 'foobar'
        assert_equal(('foo', 'bar'),
                     es.conn.transport.hosts[0]['http_auth'])

    def test_config(self):
        es = ElasticSearch(
                     host='http://127.0.1.1:9202',
                     index='foobar',
                     authorization_enabled=True,
                     compatibility_mode='pre-1.0.0',
        )
        assert_equal(es.host, 'http://127.0.1.1:9202')
        assert_equal(es.index, 'foobar')
        assert_equal(es.authorization_enabled, True)
        assert_equal(es.compatibility_mode, 'pre-1.0.0')

class TestModel(object):
    def setup(self):
        es = ElasticSearch()
        es.host = 'http://127.0.1.1:9202'
        es.index = 'foobar'
        self.es = es

        class MyModel(self.es.Model):
            __type__ = 'footype'

        self.Model = MyModel

    def teardown(self):
        pass

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

    @patch('annotator.elasticsearch.elasticsearch.Elasticsearch')
    def test_op_type_create(self, es_mock):
        """Test if operation type is 'create' in absence of an id field"""
        m = self.Model(bla='blub')
        m.save()

        conn = es_mock.return_value
        call_kwargs = conn.index.call_args_list[0][1]
        assert call_kwargs['op_type'] == 'create', "Operation should be: create"

    @patch('annotator.elasticsearch.elasticsearch.Elasticsearch')
    def test_op_type_index(self, es_mock):
        """Test if operation type is 'index' when an id field is present"""
        m = self.Model(bla='blub', id=123)
        m.save()

        conn = es_mock.return_value
        call_kwargs = conn.index.call_args_list[0][1]
        assert call_kwargs['op_type'] == 'index', "Operation should be: index"
