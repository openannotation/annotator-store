from annotator import es

TYPE = 'document'
MAPPING = {
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'link': {
        'type': 'nested',
        'properties': {
            'type': {'type': 'string', 'index': 'not_analyzed'},
            'href': {'type': 'string', 'index': 'not_analyzed'},
        }
    },
    'title': {'type': 'string'}
}

class Document(es.Model):
    __type__ = TYPE
    __mapping__ = MAPPING

    @classmethod
    def get_by_url(cls, url):
        """returns the first document match for a given URL"""
        results = cls.get_all_by_urls([url])
        return results[0] if len(results) > 0 else []

    @classmethod
    def get_all_by_urls(cls, urls):
        """returns a list of documents that have any of the supplied urls
        It is only necessary for one of the supplied urls to match.
        """
        q = {
            "query": {
                "nested": {
                    "path": "link", 
                    "query": {
                        "terms": {
                            "link.href": urls
                        }
                    }
                }
            },
            "sort": [
              {
                "updated": {
                  "order": "asc"
                }
              }
            ]
        }
        res = cls.es.conn.search_raw(q, cls.es.index, cls.__type__)
        return [cls(d['_source']) for d in res['hits']['hits']]

    def urls(self):
        """Returns a list of the urls for the document"""
        return self._urls_from_links(self.get('link', []))

    def _urls_from_links(self, links):
        urls = []
        for link in links:
            urls.append(link.get('href'))
        return urls


