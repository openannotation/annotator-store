from annotator import es

MAPPING = {
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'link': {
        'properties': {
            'type': {'type': 'string', 'index': 'no'},
            'href': {'type': 'string', 'index': 'no'},
        }
    },
    'title': {'type': 'string'}
}

class Document(es.Model):
    __type__ = 'document' 
    __mapping__ = MAPPING


