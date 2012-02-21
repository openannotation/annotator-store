from datetime import datetime

from annotator import es, authz
from flask import current_app

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

class Annotation(es.Model):

    __type__ = TYPE
    __mapping__ = MAPPING

    @classmethod
    def _build_query(cls, offset=0, limit=20, _user_id=None, _consumer_key=None, **kwargs):
        q = super(Annotation, cls)._build_query(offset, limit, **kwargs)

        if current_app.config.get('AUTHZ_ON'):
            if 'filtered' not in q['query']:
                f = {'and': []}
                q['query'] = {'filtered': {'query': q['query'], 'filter': f}}

            andclause = q['query']['filtered']['filter']['and']
            andclause.append(_permissions_query(_user_id, _consumer_key))

        return q

    def save(self):
        # For brand new annotations
        _add_created(self)
        _add_default_permissions(self)

        # For all annotations about to be saved
        _add_updated(self)

        super(Annotation, self).save()


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
