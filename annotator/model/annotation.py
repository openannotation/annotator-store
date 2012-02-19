from datetime import datetime
from flask import current_app, request
import pyes

from annotator import auth
from annotator import authz

TYPE = 'annotation'
MAPPING = {
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'quote': {'type': 'string'},
    'tags': {'type': 'string', 'index_name': 'tag'},
    'text': {'type': 'string'},
    'uri': {'type': 'string', 'index': 'not_analyzed'},
    'user' : {'type': 'string', 'index' : 'not_analyzed'},
    'consumer': {'type': 'string', 'index': 'not_analyzed'},
    'ranges': {
        'index_name': 'range',
        'properties': {
            'start': {'type': 'string', 'index': 'not_analyzed'},
            'end':   {'type': 'string', 'index': 'not_analyzed'},
            'startOffset': {'type': 'integer'},
            'endOffset':   {'type': 'integer'},
        }
    },
    'permissions': {
        'index_name': 'permission',
        'properties': {
            'read':   {'type': 'string', 'index': 'not_analyzed'},
            'update': {'type': 'string', 'index': 'not_analyzed'},
            'delete': {'type': 'string', 'index': 'not_analyzed'},
            'admin':  {'type': 'string', 'index': 'not_analyzed'}
        }
    }
}

class ValidationError(Exception):
    pass

class Annotation(dict):

    def __init__(self, *args, **kwargs):
        conn, index = _get_pyes_details()
        self.conn = conn
        self.index = index
        super(Annotation, self).__init__(*args, **kwargs)

    # It would be lovely if this were called 'get', but the dict semantics
    # already define that method name.
    @classmethod
    def fetch(cls, id):
        conn, index = _get_pyes_details()

        try:
            doc = conn.get(index, TYPE, id)
        # We should be more specific than this, but pyes doesn't raise the
        # correct exception for missing documents at the moment
        except pyes.exceptions.ElasticSearchException:
            return None
        return Annotation(doc['_source'], id=id)

    @classmethod
    def _build_query(cls, offset=0, limit=20, _user_id=None, _consumer_key=None, **kwargs):
        # Base query is a filtered match_all
        f = {'and': []}
        q = {'filtered': {'query': {'match_all': {}}, 'filter': f}}

        # Add a term query for each kwarg that isn't otherwise accounted for
        for k, v in kwargs.iteritems():
            f['and'].append({'term': {k: v}})

        f['and'].append(_permissions_query(_user_id, _consumer_key))

        return {
            'sort': [{'updated': {'order': 'desc'}}], # Sort most recent first
            'from': offset,
            'size': limit,
            'query': q
        }

    @classmethod
    def search(cls, **kwargs):
        conn, index = _get_pyes_details()

        q = cls._build_query(**kwargs)
        res = conn.search(q, index, TYPE)
        docs = res['hits']['hits']
        return [cls(d['_source'], id=d['_id']) for d in docs]

    @classmethod
    def count(cls, **kwargs):
        conn, index = _get_pyes_details()

        q = cls._build_query(**kwargs)
        res = conn.count(q['query'], index, TYPE)
        return res['count']

    def _set_id(self, rhs):
        self['id'] = rhs

    def _get_id(self):
        return self.get('id')

    id = property(_get_id, _set_id)

    def save(self):
        # For brand new annotations
        if not self.id:
            _add_created(self)
            _add_default_permissions(self)
            _add_default_auth(self)

        # For all annotations about to be saved
        _add_updated(self)

        res = self.conn.index(self, self.index, TYPE, self.id)
        self.id = res['_id']

    def delete(self):
        if self.id:
            self.conn.delete(self.index, TYPE, self.id)

def _add_created(ann):
    ann['created'] = datetime.now().isoformat()

def _add_updated(ann):
    ann['updated'] = datetime.now().isoformat()

def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}

def _add_default_auth(ann):
    if 'user' not in ann:
        ann['user'] = auth.get_request_user_id(request)
    if 'consumer' not in ann:
        ann['consumer'] = auth.get_request_consumer_key(request)

def _get_pyes_details():
    conn = current_app.extensions['pyes']
    index = current_app.config['ELASTICSEARCH_INDEX']
    return conn, index

def _permissions_query(user_id=None, consumer_key=None):
    # Append permissions filter.
    # 1) world-readable annotations
    perm_q = {'term': {'permissions.read': authz.GROUP_WORLD}}

    if consumer_key:
        # 2) annotations with 'consumer' matching current consumer and
        #    consumer group readable
        ckey_q = {'and': []}
        ckey_q['and'].append({'term': {'consumer': consumer_key}})
        ckey_q['and'].append({'term': {'permissions.read': authz.GROUP_CONSUMER}})

        perm_q = {'or': [perm_q, ckey_q]}

        if user_id:
            # 3) annotations with consumer matching current consumer, user
            #    matching current user
            owner_q = {'and': []}
            owner_q['and'].append({'term': {'consumer': consumer_key}})
            owner_q['and'].append({'or': [{'term': {'user': user_id}},
                                          {'term': {'user.id': user_id}}]})
            perm_q['or'].append(owner_q)
            # 4) annotations with authenticated group readable
            perm_q['or'].append({'term': {'permissions.read': authz.GROUP_AUTHENTICATED}})
            # 5) annotations with consumer matching current consumer, user
            #    explicitly in permissions.read list
            perm_q['or'].append({'term': {'permissions.read': user_id}})

    return perm_q
