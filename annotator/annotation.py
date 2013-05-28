from annotator import es, authz
from annotator.document import Document

from flask import current_app, g

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
    },
    'document': {
        'properties': {
            'title': {'type': 'string'},
            'link': {
                'type': 'nested',
                'properties': {
                    'type': {'type': 'string', 'index': 'not_analyzed'},
                    'href': {'type': 'string', 'index': 'not_analyzed'},
                }
            },
            'dc': {
                'type': 'nested',
                'properties': {
                    # by default elastic search will try to parse this as 
                    # a date but unfortunately the data that is in the wild 
                    # may not be parsable by ES which throws an exception
                    'date': {'type': 'string', 'index': 'not_analyzed'}
                }
            }
        }
    }
}

class Annotation(es.Model):

    __type__ = TYPE
    __mapping__ = MAPPING

    def save(self, *args, **kwargs):
        _add_default_permissions(self)

        # If the annotation includes document metadata look to see if we have 
        # the document modeled already. If we don't we'll create a new one
        # If we do then we'll merge the supplied links into it.

        if self.has_key("document"):
            d = self["document"]
            uris = [link["href"] for link in d['link']]
            docs = Document.get_all_by_uris(uris)

            if len(docs) == 0:
                doc = Document(d)
                doc.save()
            else:
                doc = docs[0]
                links = d.get('link', [])
                doc.merge_links(d['link'])
                doc.save()

        super(Annotation, self).save(*args, **kwargs)

    @classmethod
    def _build_query(cls, offset=0, limit=20, **kwargs):
        q = super(Annotation, cls)._build_query(offset, limit, **kwargs)

        if current_app.config.get('AUTHZ_ON'):
            f = authz.permissions_filter(g.user)
            if not f:
                return False # Refuse to perform the query
            q['query'] = {'filtered': {'query': q['query'], 'filter': f}}

        
        # attempt to expand query to include uris for other representations
        # using information we may have on hand about the Document 

        if kwargs.has_key('uri'):
            doc = Document.get_by_uri(kwargs['uri'])
            if doc:
                new_terms = []
                terms = q['query']['filtered']['query']['filtered']['filter']['and']
                for term in terms:
                    if term['term'].has_key('uri'):
                        term = {"or": []}
                        for uri in doc.uris():
                            term["or"].append({"term": {"uri": uri}})
                    new_terms.append(term)

                q['query']['filtered']['query']['filtered']['filter']['and'] = new_terms

        return q

    @classmethod
    def _build_query_raw(cls, request):
        q, p = super(Annotation, cls)._build_query_raw(request)

        if current_app.config.get('AUTHZ_ON'):
            f = authz.permissions_filter(g.user)
            if not f:
                return {'error': "Authorization error!", 'status': 400}, None
            q['query'] = {'filtered': {'query': q['query'], 'filter': f}}

        return q, p

def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}
