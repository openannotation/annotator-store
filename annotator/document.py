from annotator import es

TYPE = 'document'
MAPPING = {
    'id': {'type': 'string', 'index': 'no'},
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'title': {'type': 'string', 'analyzer': 'standard'},
    'link': {
        'type': 'nested',
        'properties': {
            'type': {'type': 'string'},
            'href': {'type': 'string'},
        }
    },
    'dc': {
        'type': 'nested',
        'properties': {
            # by default elastic search will try to parse this as
            # a date but unfortunately the data that is in the wild
            # may not be parsable by ES which throws an exception
            'date': {'type': 'string'}
        }
    }
}


class Document(es.Model):
    __type__ = TYPE
    __mapping__ = MAPPING

    @classmethod
    def get_by_uri(cls, uri):
        """Returns the first document match for a given URI."""
        results = cls.get_all_by_uris([uri])
        return results[0] if len(results) > 0 else []

    @classmethod
    def get_all_by_uris(cls, uris):
        """
        Returns a list of documents that have any of the supplied URIs.

        It is only necessary for one of the supplied URIs to match.
        """
        q = {'query': {'nested': {'path': 'link',
                                  'query': {'terms': {'link.href': uris}}}},
             'sort': [{'updated': {'order': 'asc',
                                   # While we do always provide a mapping for
                                   # 'updated', elasticsearch will bomb if
                                   # there are no documents in the index.
                                   # Although this is an edge case, we don't
                                   # want the API to return a 500 with an empty
                                   # index, so ignore this sort instruction if
                                   # 'updated' appears unmapped due to an empty
                                   # index.
                                   'ignore_unmapped': True,}}]}

        res = cls.es.conn.search(index=cls.es.index,
                                 doc_type=cls.__type__,
                                 body=q)
        return [cls(d['_source'], id=d['_id']) for d in res['hits']['hits']]

    def uris(self):
        """Returns a list of the URIs for the document."""
        return self._uris_from_links(self.get('link', []))

    def merge_links(self, links):
        current_uris = self.uris()
        for l in links:
            if 'href' in l and 'type' in l and l['href'] not in current_uris:
                self['link'].append(l)

    @staticmethod
    def _uris_from_links(links):
        uris = []
        for link in links:
            uris.append(link.get('href'))
        return uris

    @classmethod
    def _get_all_iterative_for_uris(cls, uris):
        """
        Builds an equivalence class (Kleene-star of documents) based on
        the supplied URIs as seed uris. It loads every document for
        which at least one supplied URI matches and recursively checks
        the uris of the retrieved documents and use the new URIs as
        seed URIs for the next iteration.

        Finally returns a list of documents that have any of the
        collected URIs
        """
        documents = []
        docs_ids = set()
        all_uris = set(uris)
        new_uris = list(uris)

        while len(new_uris):
            docs = cls.get_all_by_uris(new_uris)
            new_uris = []
            for doc in docs:
                if doc['id'] not in docs_ids:
                    documents.append(doc)
                    docs_ids.add(doc['id'])

                for uri in doc.uris():
                    if uri not in all_uris:
                        new_uris.append(uri)
                        all_uris.add(uri)

        return documents

    def save(self):
        """Saves document metadata, looks for existing documents and
        merges them to maintain equivalence classes"""
        uris = self.uris()

        # Get existing documents
        docs = self._get_all_iterative_for_uris(uris)

        # Create a new document if none existed for these uris
        if len(docs) == 0:
            super(Document, self).save()
        # Merge links to a single document
        elif len(docs) == 1:
            doc = docs[0]
            links = self.get('link', [])
            doc.merge_links(links)
            super(Document, doc).save()
        # Merge the links into all
        else:
            doc = docs.pop()
            links = self.get('link', [])
            doc.merge_links(links)
            for d in docs:
                links = d.get('link', [])
                doc.merge_links(links)

            super(Document, doc).save()

            # Merge links to all docs
            for d in docs:
                d.delete()
