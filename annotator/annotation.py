from annotator import authz, document, es

TYPE = 'annotation'
MAPPING = {
    'id': {'type': 'string', 'index': 'no'},
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'quote': {'type': 'string', 'analyzer': 'standard'},
    'tags': {'type': 'string', 'index_name': 'tag'},
    'text': {'type': 'string', 'analyzer': 'standard'},
    'uri': {'type': 'string'},
    'user': {'type': 'string'},
    'consumer': {'type': 'string'},
    'ranges': {
        'index_name': 'range',
        'properties': {
            'start': {'type': 'string'},
            'end': {'type': 'string'},
            'startOffset': {'type': 'integer'},
            'endOffset': {'type': 'integer'},
        }
    },
    'permissions': {
        'index_name': 'permission',
        'properties': {
            'read': {'type': 'string'},
            'update': {'type': 'string'},
            'delete': {'type': 'string'},
            'admin': {'type': 'string'}
        }
    },
    'document': {
        'properties': document.MAPPING
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

        if 'document' in self:
            d = document.Document(self['document'])
            d.save()

        super(Annotation, self).save(*args, **kwargs)

    @classmethod
    def search_raw(cls, query=None, params=None, raw_result=False,
                   user=None, authorization_enabled=None):
        """Perform a raw Elasticsearch query

        Any ElasticsearchExceptions are to be caught by the caller.

        Keyword arguments:
        query -- Query to send to Elasticsearch
        params -- Extra keyword arguments to pass to Elasticsearch.search
        raw_result -- Return Elasticsearch's response as is
        user -- The user to filter the results for according to permissions
        authorization_enabled -- Overrides Annotation.es.authorization_enabled
        """
        if query is None:
            query = {}
        if authorization_enabled is None:
            authorization_enabled = es.authorization_enabled
        if authorization_enabled:
            f = authz.permissions_filter(user)
            if not f:
                raise RuntimeError("Authorization filter creation failed")
            filtered_query = {
                'filtered': {
                    'filter': f
                }
            }
            # Insert original query (if present)
            if 'query' in query:
                filtered_query['filtered']['query'] = query['query']
            # Use the filtered query instead of the original
            query['query'] = filtered_query

        res = super(Annotation, cls).search_raw(query=query, params=params,
                                                raw_result=raw_result)
        return res

    @classmethod
    def _build_query(cls, query=None, offset=None, limit=None, sort=None, order=None):
        if query is None:
            query = {}

        q = super(Annotation, cls)._build_query(query, offset, limit, sort, order)

        # attempt to expand query to include uris for other representations
        # using information we may have on hand about the Document
        if 'uri' in query:
            clauses = q['query']['bool']
            doc = document.Document.get_by_uri(query['uri'])
            if doc:
                for clause in clauses['must']:
                    # Rewrite the 'uri' clause to match any of the document URIs
                    if 'match' in clause and 'uri' in clause['match']:
                        uri_matchers = []
                        for uri in doc.uris():
                            uri_matchers.append({'match': {'uri': uri}})
                        del clause['match']
                        clause['bool'] = {
                            'should': uri_matchers,
                            'minimum_should_match': 1
                        }

        return q


def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}
