from datetime import datetime
import pyes

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

def make_model(conn, index='annotator', authz_on=True):
    return type('Annotation', (_Annotation,), {
        'conn': conn,
        'index': index,
        'authz_on': authz_on
    })

class ValidationError(Exception):
    pass

class _Annotation(dict):
    conn = None  # set by make_model
    index = None # set by make_model

    @classmethod
    def create_all(cls):
        cls.conn.create_index_if_missing(cls.index)
        cls.conn.put_mapping(TYPE, {'properties': MAPPING}, cls.index)

    @classmethod
    def drop_all(cls):
        cls.conn.delete_index_if_exists(cls.index)

    # It would be lovely if this were called 'get', but the dict semantics
    # already define that method name.
    @classmethod
    def fetch(cls, id):
        try:
            doc = cls.conn.get(cls.index, TYPE, id)
        # We should be more specific than this, but pyes doesn't raise the
        # correct exception for missing documents at the moment
        except pyes.exceptions.ElasticSearchException:
            return None
        return cls(doc['_source'], id=id)

    @classmethod
    def _build_query(cls, offset=0, limit=20, _user_id=None, _consumer_key=None, **kwargs):
        # Base query is a filtered match_all
        q = {'match_all': {}}

        if kwargs or cls.authz_on:
            f = {'and': []}
            q = {'filtered': {'query': q, 'filter': f}}

        # Add a term query for each kwarg that isn't otherwise accounted for
        for k, v in kwargs.iteritems():
            q['filtered']['filter']['and'].append({'term': {k: v}})

        if cls.authz_on:
            q['filtered']['filter']['and'].append(_permissions_query(_user_id, _consumer_key))

        return {
            'sort': [{'updated': {'order': 'desc'}}], # Sort most recent first
            'from': offset,
            'size': limit,
            'query': q
        }

    @classmethod
    def search(cls, **kwargs):
        q = cls._build_query(**kwargs)
        res = cls.conn.search(q, cls.index, TYPE)
        docs = res['hits']['hits']
        return [cls(d['_source'], id=d['_id']) for d in docs]

    @classmethod
    def count(cls, **kwargs):
        q = cls._build_query(**kwargs)
        res = cls.conn.count(q['query'], cls.index, TYPE)
        return res['count']

    def _set_id(self, rhs):
        self['id'] = rhs

    def _get_id(self):
        return self.get('id')

    id = property(_get_id, _set_id)

    def save(self):
        # For brand new annotations
        _add_created(self)
        _add_default_permissions(self)

        # For all annotations about to be saved
        _add_updated(self)

        res = self.conn.index(self, self.index, TYPE, self.id)
        self.id = res['_id']

    def delete(self):
        if self.id:
            self.conn.delete(self.index, TYPE, self.id)

def _add_created(ann):
    if 'created' not in ann:
        ann['created'] = datetime.now().isoformat()

def _add_updated(ann):
    ann['updated'] = datetime.now().isoformat()

def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}

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
