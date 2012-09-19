import csv
import json
import logging

import pyes
from flask import _app_ctx_stack

from annotator.atoi import atoi

log = logging.getLogger(__name__)

RESULTS_MAX_SIZE = 200

class ElasticSearch(object):

    """

    Thin wrapper around an ElasticSearch connection to make connection handling
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

    def init_app(self, app):
        app.config.setdefault('ELASTICSEARCH_HOST', 'http://127.0.0.1:9200')
        app.config.setdefault('ELASTICSEARCH_INDEX', app.name)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['elasticsearch'] = self

    def get_app(self):
        """

        Helper method that implements the logic to look up an application.

        """
        if self.app is not None:
            return self.app
        ctx = _app_ctx_stack.top
        if ctx is not None:
            return ctx.app
        raise RuntimeError('application not registered on ElasticSearch '
                           'instance and no application bound to current '
                           'context')

    def get_conn(self, app):
        host = app.config['ELASTICSEARCH_HOST']
        # We specifically set decoder to prevent pyes from futzing with
        # datetimes.
        conn = pyes.ES(host, decoder=json.JSONDecoder)
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
        try:
            cls.es.conn.create_index_if_missing(cls.es.index)
        except pyes.exceptions.ElasticSearchException:
            log.warn('Index creation failed. If you are running against Bonsai Elasticsearch, this is expected and ignorable.')
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
        except pyes.exceptions.NotFoundException:
            return None
        return cls(doc, id=id)

    @classmethod
    def _build_query(cls, offset=0, limit=20, **kwargs):
        return _build_query(offset, limit, kwargs)

    @classmethod
    def _build_query_raw(cls, request):
        return _build_query_raw(request)

    @classmethod
    def search(cls, **kwargs):
        q = cls._build_query(**kwargs)
        if not q:
            return []
        res = cls.es.conn.search_raw(q, cls.es.index, cls.__type__)
        docs = res['hits']['hits']
        return [cls(d['_source'], id=d['_id']) for d in docs]

    @classmethod
    def search_raw(cls, request):
        q, params = cls._build_query_raw(request)
        if 'error' in q:
            return q
        try:
            res = cls.es.conn.search_raw(q, cls.es.index, cls.__type__, **params)
        except pyes.exceptions.ElasticSearchException as e:
            return e.result
        else:
            return res

    @classmethod
    def count(cls, **kwargs):
        q = cls._build_query(**kwargs)
        if not q:
            return 0
        res = cls.es.conn.count(q['query'], cls.es.index, cls.__type__)
        return res['count']

    def _set_id(self, rhs):
        self['id'] = rhs

    def _get_id(self):
        return self.get('id')

    id = property(_get_id, _set_id)

    def save(self, refresh=True):
        res = self.es.conn.index(self, self.es.index, self.__type__, self.id)
        self.id = res['_id']
        if refresh:
            self.es.conn.refresh()

    def delete(self):
        if self.id:
            self.es.conn.delete(self.es.index, self.__type__, self.id)

def make_model(es):
    return type('Model', (_Model,), {'es': es})

def _csv_split(s, delimiter=','):
    return [r for r in csv.reader([s], delimiter=delimiter)][0]

def _build_query(offset, limit, kwds):
    # Base query is a filtered match_all
    q = {'match_all': {}}

    if kwds:
        f = {'and': []}
        q = {'filtered': {'query': q, 'filter': f}}

    # Add a term query for each keyword
    for k, v in kwds.iteritems():
        q['filtered']['filter']['and'].append({'term': {k: v}})

    return {
        'sort': [{'updated': {'order': 'desc'}}], # Sort most recent first
        'from': max(0, offset),
        'size': min(RESULTS_MAX_SIZE, max(0, limit)),
        'query': q
    }

def _build_query_raw(request):
    query = {}
    params = {}

    if request.method == 'GET':
        for k, v in request.args.iteritems():
            _update_query_raw(query, params, k, v)

    elif request.method == 'POST':

        try:
            query = json.loads(request.json or request.data or request.form.keys()[0])
        except (ValueError, IndexError):
            return {'error': 'Could not parse request payload!', 'status': 400}, None

        params = request.args

    for o in (params, query):
        if 'from' in o:
            o['from'] = max(0, atoi(o['from']))
        if 'size' in o:
            o['size'] = min(RESULTS_MAX_SIZE, max(0, atoi(o['size'])))

    return query, params

def _update_query_raw(qo, params, k, v):
    if 'query' not in qo:
        qo['query'] = {}
    q = qo['query']

    if 'query_string' not in q:
        q['query_string'] = {}
    qs = q['query_string']

    if k == 'q':
        qs['query'] = v

    elif k == 'df':
        qs['default_field'] = v

    elif k in ('explain', 'track_scores', 'from', 'size', 'timeout',
               'lowercase_expanded_terms', 'analyze_wildcard'):
        qo[k] = v

    elif k == 'fields':
        qo[k] = _csv_split(v)

    elif k == 'sort':
        if 'sort' not in r:
            qo[k] = []

        split = _csv_split(v, ':')

        if len(split) == 1:
            qo[k].append(split[0])
        else:
            fld = ':'.join(split[0:-1])
            drn = split[-1]
            qo[k].append({fld: drn})

    elif k == 'search_type':
        params[k] = v
