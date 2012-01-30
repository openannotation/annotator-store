from datetime import datetime
import pyes

conn = None
index = None

TYPE = 'annotation'
MAPPING = {
    'annotator_schema_version': {'type': 'string', 'null_value': 'v1.0'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'quote': {'type': 'string'},
    'tags': {'type': 'string', 'index_name': 'tag'},
    'text': {'type': 'string'},
    'uri': {'type': 'string', 'index': 'not_analyzed'},
    'user' : {'type': 'string', 'index' : 'not_analyzed'},
    'ranges': {
        'index_name': 'range',
        'properties': {
            'start': {'type': 'string', 'index': 'not_analyzed'},
            'end':   {'type': 'string', 'index': 'not_analyzed'},
            'startOffset': {'type': 'integer'},
            'endOffset':   {'type': 'integer'},
        }
    }
}

def configure(c, config):
    global conn, index
    conn = c
    index = config['ELASTICSEARCH_INDEX']

class ValidationError(Exception):
    pass

class Annotation(dict):

    # It would be lovely if this were called 'get', but the dict semantics
    # already define that method name.
    @classmethod
    def fetch(cls, id):
        try:
            doc = conn.get(index, TYPE, id)
        # We should be more specific than this, but pyes doesn't raise the
        # correct exception for missing documents at the moment
        except pyes.exceptions.ElasticSearchException:
            return None
        return Annotation(doc['_source'], id=id)

    @classmethod
    def _build_query(cls, limit=20, **kwargs):
        q = {'match_all': {}}

        if kwargs:
            f = {'and': [{'term': {k: v}} for k, v in kwargs.iteritems()]}
            q = {'filtered': {'query': q, 'filter': f}}

        return {
            # Sort most recent first
            'sort': [{'updated': {'order': 'desc'}}],
            'size': limit,
            'query': q
        }

    @classmethod
    def search(cls, limit=20, **kwargs):
        q = cls._build_query(limit, **kwargs)
        res = conn.search(q, index, TYPE)
        docs = res['hits']['hits']
        return [cls(d['_source'], id=d['_id']) for d in docs]

    @classmethod
    def count(cls, **kwargs):
        q = cls._build_query(**kwargs)
        res = conn.count(q['query'], index, TYPE)
        return res['count']

    def _set_id(self, rhs):
        self['id'] = rhs

    def _get_id(self):
        return self.get('id')

    id = property(_get_id, _set_id)

    def save(self):
        _add_created(self)
        _add_updated(self)

        res = conn.index(self, index, TYPE, self.id)
        self.id = res['_id']

    def delete(self):
        if self.id:
            conn.delete(index, TYPE, self.id)

def _add_created(ann):
    if 'created' not in ann:
        ann['created'] = datetime.now().isoformat()

def _add_updated(ann):
    ann['updated'] = datetime.now().isoformat()
