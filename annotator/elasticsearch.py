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
                 authorization_enabled = False):
        self.host = host
        self.index = index
        self.authorization_enabled = authorization_enabled

        self.Model = make_model(self)

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

    def drop_all(self):
        """Delete the index and its contents"""
        if self.conn.indices.exists(self.index):
            self.conn.indices.close(self.index)
            self.conn.indices.delete(self.index)

    def create_models(self, models):
        mappings = _compile_mappings(models)
        analysis = _compile_analysis(models)

        # If it does not yet exist, simply create the index
        try:
            response = self.conn.indices.create(self.index, ignore=400, body={
                'mappings': mappings,
                'settings': {'analysis': analysis},
            })
            return
        except elasticsearch.exceptions.ConnectionError as e:
            msg = ('Can not access ElasticSearch at {0}! '
                   'Check to ensure it is running.').format(self.host)
            raise elasticsearch.exceptions.ConnectionError('N/A', msg, e)

        # Bad request (400) is ignored above, to prevent warnings in the log
        # when the index already exists, but the failure could be for other
        # reasons. If so, raise the error here.
        if 'error' in response and 'IndexAlreadyExists' not in response['error']:
            raise elasticsearch.exceptions.RequestError(400, response['error'])

        # Update the mappings of the existing index
        self._update_analysis(analysis)
        self._update_mappings(mappings)

    def _update_analysis(self, analysis):
        """Update analyzers and filters"""
        settings = self.conn.indices.get_settings(index=self.index)
        existing = settings[self.index]['settings']['index']['analysis']
        # Only bother if new settings would differ from existing settings
        if not self._analysis_up_to_date(existing, analysis):
            try:
                self.conn.indices.close(index=self.index)
                self.conn.indices.put_settings(index=self.index,
                                               body={'analysis': analysis})
            finally:
                self.conn.indices.open(index=self.index)

    def _update_mappings(self, mappings):
        """Update mappings.

        Warning: can explode because of a MergeMappingError when mappings are
        incompatible"""
        for doc_type, body in mappings.items():
            self.conn.indices.put_mapping(
                index=self.index,
                doc_type=doc_type,
                body=body
            )

    @staticmethod
    def _analysis_up_to_date(existing, analysis):
        """Tell whether existing settings are up to date"""
        new_analysis = existing.copy()
        for section, items in analysis.items():
            new_analysis.setdefault(section,{}).update(items)
        return new_analysis == existing


class _Model(dict):
    """Base class that represents a document type in an ElasticSearch index.

       A child class is expected to define these two attributes:
       __type__ -- The name of the document type
       __mapping__ -- A mapping of the document's fields

       Mapping:
       One field, 'id', is treated specially. Its value will not be stored,
       but be used as the _id identifier of the document in Elasticsearch. If
       an item is indexed without providing an id, the _id is automatically
       generated by ES.

       Unmapped fields: Fields that are not defined in the mapping are analyzed
       using the 'keyword' analyzer, which practically means no analysis is
       performed: searching for these fields will be exact and case sensitive.
       To make a field full-text searchable, its mapping should configure it
       with 'analyzer':'standard'.
    """

    @classmethod
    def get_mapping(cls):
        return {
            cls.__type__: {
                '_id': {
                    'path': 'id',
                },
                '_source': {
                    'excludes': ['id'],
                },
                'analyzer': 'keyword',
                'properties': cls.__mapping__,
            }
        }

    @classmethod
    def get_analysis(cls):
        return getattr(cls, '__analysis__', {})

    # It would be lovely if this were called 'get', but the dict semantics
    # already define that method name.
    @classmethod
    def fetch(cls, id):
        try:
            doc = cls.es.conn.get(index=cls.es.index,
                                  doc_type=cls.__type__,
                                  id=id)
        except elasticsearch.exceptions.NotFoundError:
            return None
        return cls(doc['_source'], id=id)

    @classmethod
    def _build_query(cls, query=None, offset=None, limit=None):
        if offset is None:
            offset = 0
        if limit is None:
            limit = RESULTS_DEFAULT_SIZE
        if query is None:
            query = {}
        return _build_query(query, offset, limit)

    @classmethod
    def search(cls, query=None, offset=0, limit=RESULTS_DEFAULT_SIZE, **kwargs):
        q = cls._build_query(query=query, offset=offset, limit=limit)
        if not q:
            return []
        return cls.search_raw(q, **kwargs)

    @classmethod
    def search_raw(cls, query=None, params=None, raw_result=False):
        """Perform a raw Elasticsearch query

        Any ElasticsearchExceptions are to be caught by the caller.

        Keyword arguments:
        query -- Query to send to Elasticsearch
        params -- Extra keyword arguments to pass to Elasticsearch.search
        raw_result -- Return Elasticsearch's response as is
        """
        if query is None:
            query = {}
        if params is None:
            params = {}
        res = cls.es.conn.search(index=cls.es.index,
                                 doc_type=cls.__type__,
                                 body=query,
                                 **params)
        if not raw_result:
            docs = res['hits']['hits']
            res = [cls(d['_source'], id=d['_id']) for d in docs]
        return res

    @classmethod
    def count(cls, **kwargs):
        """Like search, but only count the number of matches."""
        kwargs.setdefault('params', {})
        kwargs['params'].update({'search_type':'count'})
        res = cls.search(raw_result=True, **kwargs)
        return res['hits']['total']

    def save(self, refresh=True):
        _add_created(self)
        _add_updated(self)

        if not 'id' in self:
            op_type = 'create'
        else:
            op_type = 'index'

        res = self.es.conn.index(index=self.es.index,
                                 doc_type=self.__type__,
                                 body=self,
                                 op_type=op_type,
                                 refresh=refresh)
        self['id'] = res['_id']

    def delete(self):
        if 'id' in self:
            self.es.conn.delete(index=self.es.index,
                                doc_type=self.__type__,
                                id=self['id'])


def make_model(es):
    return type('Model', (_Model,), {'es': es})


def _compile_mappings(models):
    """Collect the mappings from the models"""
    mappings = {}
    for model in models:
        mappings.update(model.get_mapping())
    return mappings


def _compile_analysis(models):
    """Merge the custom analyzers and such from the models"""
    analysis = {}
    for model in models:
        for section, items in model.get_analysis().items():
            existing_items = analysis.setdefault(section, {})
            for name in items:
                if name in existing_items:
                    fmt = "Duplicate definition of 'index.analysis.{}.{}'."
                    msg = fmt.format(section, name)
                    raise RuntimeError(msg)
            existing_items.update(items)
    return analysis


def _csv_split(s, delimiter=','):
    return [r for r in csv.reader([s], delimiter=delimiter)][0]


def _build_query(query, offset, limit):
    # Create a match query for each keyword
    match_clauses = [{'match': {k: v}} for k, v in iteritems(query)]

    if len(match_clauses) == 0:
        # Elasticsearch considers an empty conjunction to be false..
        match_clauses.append({'match_all': {}})

    return {
        'sort': [{'updated': {
            # Sort most recent first
            'order': 'desc',
            # While we do always provide a mapping for 'updated', elasticsearch
            # will bomb if there are no documents in the index. Although this
            # is an edge case, we don't want the API to return a 500 with an
            # empty index, so ignore this sort instruction if 'updated' appears
            # unmapped due to an empty index.
            'ignore_unmapped': True,
        }}],
        'from': max(0, offset),
        'size': min(RESULTS_MAX_SIZE, max(0, limit)),
        'query': {'bool': {'must': match_clauses}}
    }


def _add_created(ann):
    if 'created' not in ann:
        ann['created'] = datetime.datetime.now(iso8601.iso8601.UTC).isoformat()


def _add_updated(ann):
    ann['updated'] = datetime.datetime.now(iso8601.iso8601.UTC).isoformat()
