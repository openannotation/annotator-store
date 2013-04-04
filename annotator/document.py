from annotator import es

TYPE = 'document'
MAPPING = {
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'link': {
        'properties': {
            'type': {'type': 'string'},
            'href': {'type': 'string'},
        }
    },
    'title': {'type': 'string'}
}

class Document(es.Model):
    __type__ = TYPE
    __mapping__ = MAPPING


