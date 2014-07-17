from __future__ import absolute_import

import csv
import json
import logging
import datetime

import iso8601

import elasticsearch
from six import iteritems
from six.moves.urllib.parse import urlparse
from annotator.atoi import atoi

log = logging.getLogger(__name__)

RESULTS_MAX_SIZE = 200
RESULTS_DEFAULT_SIZE = 20

class ElasticSearch(object):
    """
    Thin wrapper around an ElasticSearch connection to make connection handling
    more convenient.

    Settings for the ES host and index name etcetera can still be changed in the
    corresponding attributes before the connection (self.conn) is used.
    """

    def __init__(self,
                 host = 'http://127.0.0.1:9200',
                 index = 'annotator',
                 authorization_enabled = False,
                 compatibility_mode = None):
        self.host = host
        self.index = index
        self.authorization_enabled = authorization_enabled
        self.compatibility_mode = compatibility_mode

    def _connect(self):
        host = self.host
        parsed = urlparse(host)

        connargs = {
          'host': parsed.hostname,
        }

        username = parsed.username
        password = parsed.password
        if username is not None or password is not None:
            connargs['http_auth'] = ((username or ''), (password or ''))

        if parsed.port is not None:
            connargs['port'] = parsed.port

        if parsed.path:
            connargs['url_prefix'] = parsed.path

        conn = elasticsearch.Elasticsearch(
            hosts=[connargs],
            connection_class=elasticsearch.Urllib3HttpConnection)
        return conn

    @property
    def conn(self):
        if not hasattr(self, '_connection'):
            self._connection = self._connect()
        return self._connection


class Model(dict):

    @classmethod
    def create_all(cls, es):
        logging.info("creating index " + es.index)
        try:
            es.conn.indices.create(es.index)
        except elasticsearch.exceptions.RequestError as e:
            # Reraise anything that isn't just a notification that the index
            # already exists
            if not e.error.startswith('IndexAlreadyExistsException'):
                raise
            log.warn('Index creation failed as index already exists. If you '
                     'are running against Bonsai Elasticsearch, this is '
                     'expected and ignorable.')
        mapping = {cls.__type__: {'properties': cls.__mapping__}}
        es.conn.indices.put_mapping(index=es.index,
                                    doc_type=cls.__type__,
                                    body=mapping)

    @classmethod
    def drop_all(cls, es):
        if es.conn.indices.exists(es.index):
            es.conn.indices.close(es.index)
            es.conn.indices.delete(es.index)

    # It would be lovely if this were called 'get', but the dict semantics
    # already define that method name.
    @classmethod
    def fetch(cls, es, id):
        try:
            doc = es.conn.get(index=es.index,
                              doc_type=cls.__type__,
                              id=id)
        except elasticsearch.exceptions.NotFoundError:
            return None
        return cls(doc['_source'], id=id)

    @classmethod
    def _build_query(cls, es, query=None, offset=None, limit=None, **kwargs):
        if offset is None:
            offset = 0
        if limit is None:
            limit = RESULTS_DEFAULT_SIZE
        if query is None:
            query = {}
        return _build_query(query, offset, limit)

    @classmethod
    def _build_query_raw(cls, es, request, **kwargs):
        return _build_query_raw(request)

    @classmethod
    def search(cls, es, query=None, offset=0, limit=RESULTS_DEFAULT_SIZE,
               **kwargs):
        q = cls._build_query(es, query=query, offset=offset, limit=limit,
                             **kwargs)
        if not q:
            return []
        logging.debug("doing search: %s", q)
        res = es.conn.search(index=es.index,
                             doc_type=cls.__type__,
                             body=q)
        docs = res['hits']['hits']
        return [cls(d['_source'], id=d['_id']) for d in docs]

    @classmethod
    def search_raw(cls, es, request, **kwargs):
        q, params = cls._build_query_raw(es, request, **kwargs)
        if 'error' in q:
            return q
        try:
            res = es.conn.search(index=es.index,
                                 doc_type=cls.__type__,
                                 body=q,
                                 **params)
        except elasticsearch.exceptions.ElasticsearchException as e:
            return e.result
        else:
            return res

    @classmethod
    def count(cls, es, **kwargs):
        q = cls._build_query(es, **kwargs)
        if not q:
            return 0

        # Extract the query, and wrap it in the expected object. This has the
        # effect of removing sort or paging parameters that aren't allowed by
        # the count API.
        q = {'query': q['query']}

        # In elasticsearch prior to 1.0.0, the payload to `count` was a bare
        # query.
        if es.compatibility_mode == 'pre-1.0.0':
            q = q['query']

        res = es.conn.count(index=es.index,
                            doc_type=cls.__type__,
                            body=q)
        return res['count']

    def _set_id(self, rhs):
        self['id'] = rhs

    def _get_id(self):
        return self.get('id')

    id = property(_get_id, _set_id)

    def save(self, es, refresh=True):
        _add_created(self)
        _add_updated(self)
        res = es.conn.index(index=es.index,
                            doc_type=self.__type__,
                            id=self.id,
                            body=self,
                            refresh=refresh)
        self.id = res['_id']

    def delete(self, es):
        if self.id:
            es.conn.delete(index=es.index,
                           doc_type=self.__type__,
                           id=self.id)


def _csv_split(s, delimiter=','):
    return [r for r in csv.reader([s], delimiter=delimiter)][0]


def _build_query(query, offset, limit):
    # Base query is a filtered match_all
    q = {'match_all': {}}

    if query:
        f = {'and': []}
        q = {'filtered': {'query': q, 'filter': f}}

    # Add a term query for each keyword
    for k, v in iteritems(query):
        q['filtered']['filter']['and'].append({'term': {k: v}})

    return {
        'sort': [{'updated': {'order': 'desc'}}],  # Sort most recent first
        'from': max(0, offset),
        'size': min(RESULTS_MAX_SIZE, max(0, limit)),
        'query': q
    }


def _build_query_raw(request):
    query = {}
    params = {}

    if request.method == 'GET':
        for k, v in iteritems(request.args):
            _update_query_raw(query, params, k, v)

        if 'query' not in query:
            query['query'] = {'match_all': {}}

    elif request.method == 'POST':

        try:
            query = json.loads(request.json or
                               request.data or
                               request.form.keys()[0])
        except (ValueError, IndexError):
            return ({'error': 'Could not parse request payload!',
                     'status': 400},
                    None)

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
        if 'sort' not in qo:
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


def _add_created(ann):
    if 'created' not in ann:
        ann['created'] = datetime.datetime.now(iso8601.iso8601.UTC).isoformat()


def _add_updated(ann):
    ann['updated'] = datetime.datetime.now(iso8601.iso8601.UTC).isoformat()
