from threading import Lock

import pyes
from flask import _request_ctx_stack

class ElasticSearch(object):

    """Thin wrapper around an ElasticSearch connection to make connection handling
    transparent in a Flask application. Usage:

        app = Flask(__name__)
        es = ElasticSearch(app)

    Or, you can bind the object to the application later:

        es = ElasticSearch()

        def create_app():
            app = Flask(__name__)
            es.init_app(app)
            return app
    """

    def __init__(self, app=None):
        if app is not None:
            self.app = app
            self.init_app(app)
        else:
            self.app = None

        self.Model = make_model(self)
        self._connection_lock = Lock()

    def init_app(self, app):
        app.config.setdefault('ELASTICSEARCH_HOST', '127.0.0.1:9200')
        app.config.setdefault('ELASTICSEARCH_INDEX', app.name)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['elasticsearch'] = self

    def get_app(self):
        """Helper method that implements the logic to look up an application.
        """
        if self.app is not None:
            return self.app
        ctx = _request_ctx_stack.top
        if ctx is not None:
            return ctx.app
        raise RuntimeError('application not registered on ElasticSearch '
                           'instance and no application bound to current '
                           'context')

    def get_conn(self, app):
        with self._connection_lock:
            host = app.config['ELASTICSEARCH_HOST']
            conn = pyes.ES(host)
            return conn

    @property
    def conn(self):
        return self.get_conn(self.get_app())

    @property
    def index(self):
        return self.get_app().config['ELASTICSEARCH_INDEX']


class _Model(dict):
    @classmethod
    def create_all(cls):
        cls.es.conn.create_index_if_missing(cls.es.index)
        cls.es.conn.put_mapping(cls.__type__, {'properties': cls.__mapping__}, cls.es.index)

    @classmethod
    def drop_all(cls):
        cls.es.conn.delete_index_if_exists(cls.es.index)

    # It would be lovely if this were called 'get', but the dict semantics
    # already define that method name.
    @classmethod
    def fetch(cls, id):
        try:
            doc = cls.es.conn.get(cls.es.index, cls.__type__, id)
        # We should be more specific than this, but pyes doesn't raise the
        # correct exception for missing documents at the moment
        except pyes.exceptions.ElasticSearchException:
            return None
        return cls(doc['_source'], id=id)

    @classmethod
    def _build_query(cls, offset=0, limit=20, **kwargs):
        offset = max(0, offset)
        limit = min(200, max(0, limit))

        # Base query is a filtered match_all
        q = {'match_all': {}}

        if kwargs:
            f = {'and': []}
            q = {'filtered': {'query': q, 'filter': f}}

        # Add a term query for each kwarg that isn't otherwise accounted for
        for k, v in kwargs.iteritems():
            q['filtered']['filter']['and'].append({'term': {k: v}})

        return {
            'sort': [{'updated': {'order': 'desc'}}], # Sort most recent first
            'from': offset,
            'size': limit,
            'query': q
        }

    @classmethod
    def search(cls, **kwargs):
        q = cls._build_query(**kwargs)
        res = cls.es.conn.search(q, cls.es.index, cls.__type__)
        docs = res['hits']['hits']
        return [cls(d['_source'], id=d['_id']) for d in docs]

    @classmethod
    def count(cls, **kwargs):
        q = cls._build_query(**kwargs)
        res = cls.es.conn.count(q['query'], cls.es.index, cls.__type__)
        return res['count']

    def _set_id(self, rhs):
        self['id'] = rhs

    def _get_id(self):
        return self.get('id')

    id = property(_get_id, _set_id)

    def save(self):
        res = self.es.conn.index(self, self.es.index, self.__type__, self.id)
        self.id = res['_id']

    def delete(self):
        if self.id:
            self.es.conn.delete(self.es.index, self.__type__, self.id)

def make_model(es):
    return type('Model', (_Model,), {'es': es})
