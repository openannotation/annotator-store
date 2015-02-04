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
MAX_ITERATIONS = 5


class Document(es.Model):
    __type__ = TYPE
    __mapping__ = MAPPING

    @classmethod
    def get_by_uri(cls, uri):
        """Returns the first document match for a given URI."""
        results = cls._get_all_by_uris([uri])
        return results[0] if len(results) > 0 else []

    @classmethod
    def _get_all_by_uris(cls, uris):
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
        documents = {}
        all_uris = set(uris)
        new_uris = list(uris)
        iterations = 0

        while len(new_uris) and iterations < MAX_ITERATIONS:
            docs = cls._get_all_by_uris(new_uris)
            new_uris = []
            for doc in docs:
                if doc['id'] not in documents:
                    documents[doc['id']] = doc

                    for uri in doc.uris():
                        if uri not in all_uris:
                            new_uris.append(uri)
                            all_uris.add(uri)
            iterations += 1

        return list(documents.values())

    def _remove_deficient_links(self):
        # Remove links without a type or href
        links = self.get('link', [])
        filtered_list = [l for l in links if 'type' in l and 'href' in l]
        self['link'] = filtered_list

    @classmethod
    def _fill_bulk_header(cls, document):
        return {
            '_index': cls.es.index,
            '_type': cls.__type__,
            '_id': document['id']
        }

    @classmethod
    def _bulk_operation(cls, to_delete, to_index):
        bulk_list = []

        for doc_to_delete in to_delete:
            bulk_item = {'delete': cls._fill_bulk_header(doc_to_delete)}
            bulk_list.append(bulk_item)

        for doc_to_index in to_index:
            bulk_item = {'index': cls._fill_bulk_header(doc_to_index)}
            index_item = doc_to_index

            bulk_list.append(bulk_item)
            bulk_list.append(index_item)

        cls.es.conn.bulk(body=bulk_list, refresh=True)

    def save(self):
        """Saves document metadata, looks for existing documents and
        merges them to maintain equivalence classes"""
        self._remove_deficient_links()
        uris = self.uris()

        # Get existing documents
        existing_docs = self._get_all_iterative_for_uris(uris)

        # Create a new document if none existed for these uris
        if len(existing_docs) == 0:
            super(Document, self).save()
        # Merge links from all docs into this
        else:
            for d in existing_docs:
                links = d.get('link', [])
                self.merge_links(links)

            self._bulk_operation(existing_docs, [])
            # A separate operation because we want to save
            # the document id if it didn't have any before
            super(Document, self).save()
