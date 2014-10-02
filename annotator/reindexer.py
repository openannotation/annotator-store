from __future__ import absolute_import

from elasticsearch import helpers

from .annotation import Annotation
from .document import Document

class Reindexer(object):

    es_models = Annotation, Document

    def __init__(self, conn, interactive=False):
        self.conn = conn
        self.interactive = interactive

    def _print(self, s):
        if self.interactive:
            print(s)

    def _ask(self, s):
        if self.interactive:
            return raw_input(s + " (y/N) ").strip().lower().startswith('y')
        else:
            return True


    def reindex(self, old_index, new_index):
        """Reindex documents using the current mappings."""
        conn = self.conn

        if not conn.indices.exists(old_index):
            raise ValueError("Index {0} does not exist!".format(old_index))

        if conn.indices.exists(new_index):
            raise ValueError("Index {0} already exists!".format(new_index))

        # Create the new index
        conn.indices.create(new_index)

        # Apply the new mappings
        self.put_mappings(new_index)

        # Do the actual reindexing.
        self._print("Reindexing {0} to {1}..".format(old_index, new_index))
        helpers.reindex(conn, old_index, new_index)
        self._print("Reindexing done.")

    def alias(self, index, alias):
        self._print("Creating alias {alias} to point to {index}.."
                    .format(alias=alias, index=index))
        self.conn.indices.put_alias(name=alias, index=index)

    def delete(self, index_or_alias):
        """Delete an index or alias"""
        conn = self.conn
        # Look if it is a real index or an alias
        is_alias = conn.indices.exists_alias(index_or_alias)
        if is_alias:
            # Remove the alias.
            real_index = ','.join(conn.indices.get_alias(index_or_alias).keys())
            self._print("Deleting alias {index_or_alias}.. (was an alias for {real_index})"
                        .format(index_or_alias=index_or_alias, real_index=real_index))
            conn.indices.delete_alias(name=index_or_alias, index='_all')
        else:
            # Delete the index.
            self._print("Deleting index {index}..".format(index=index_or_alias))
            conn.indices.delete(index_or_alias)


    def put_mappings(self, index):
        conn = self.conn
        for model in self.es_models:
            mapping = model.get_mapping()
            # Apply mapping
            conn.indices.put_mapping(index=index,
                                     doc_type=model.__type__,
                                     body=mapping)
