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

        while len(new_uris):
            docs = cls._get_all_by_uris(new_uris)
            new_uris = []
            for doc in docs:
                if doc['id'] not in documents:
                    documents[doc['id']] = doc

                    for uri in doc.uris():
                        if uri not in all_uris:
                            new_uris.append(uri)
                            all_uris.add(uri)

        return list(documents.values())

    def _remove_deficient_links(self):
        # Remove links without a type or href
        links = self.get('link', [])
        filtered_list = [l for l in links if 'type' in l and 'href' in l]
        self['link'] = filtered_list

    @classmethod
    def _bulk_delete_and_update(cls, to_delete, to_update):
        bulk_list = []

        for doc_to_delete in to_delete:
            bulk_item = {
                'delete': {
                    '_index': cls.es.index,
                    '_type': cls.__type__,
                    '_id': doc_to_delete['id']
                }
            }
            bulk_list.append(bulk_item)

        for doc_to_update in to_update:
            bulk_item = {
                'update': {
                    '_index': cls.es.index,
                    '_type': cls.__type__,
                    '_id': doc_to_update['id'],
                }
            }

            update_item = {
                'doc': doc_to_update
            }

            bulk_list.append(bulk_item)
            bulk_list.append(update_item)

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
        # Merge links to a single document
        elif len(existing_docs) == 1:
            super_doc = existing_docs[0]
            links = self.get('link', [])
            super_doc.merge_links(links)
            super(Document, super_doc).save()
        # Merge links from all docs into one
        else:
            super_doc = existing_docs.pop()
            links = self.get('link', [])
            super_doc.merge_links(links)
            for d in existing_docs:
                links = d.get('link', [])
                super_doc.merge_links(links)

            self._bulk_delete_and_update(existing_docs, [super_doc])
