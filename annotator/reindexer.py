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


    def reindex(self, old_index, new_index):
        conn = self.conn

        if old_index == new_index:
            self.reindex_in_place(old_index)
            return

        if not conn.indices.exists(old_index):
            raise ValueError("Index {0} does not exist!".format(old_index))

        if conn.indices.exists(new_index):
            raise ValueError("Index {0} already exists!".format(new_index))

        # Create the new index
        conn.indices.create(new_index)

        # Apply the new settings and mappings
        self.put_mappings(new_index)

        # Do the actual reindexing.
        self._print("Reindexing {0} to {1}..".format(old_index, new_index))
        helpers.reindex(conn, old_index, new_index)
        self._print("Reindexing done.")


    def reindex_in_place(self, index):
        """Fiddle with aliases to pretend an in-place reindexing."""
        conn = self.conn

        # Pick an arbitrary unused name for the real new index
        new_index = index + '_real'
        # If it already exists, append a number to it.
        suffix_number = 0
        while conn.indices.exists(new_index) is True:
            suffix_number += 1
            if suffix_number >= 10:
                # Something's probably wrong (we may be in an infinite loop?)
                raise RuntimeError("Desired index names are occupied, please clean up your old indices!")
            new_index = '%s_real%d' % (index, suffix_number)

        # Look if current index is a real index or an alias
        index_is_alias = conn.indices.exists_alias(index)
        if index_is_alias:
            real_index = ','.join(conn.indices.get_alias(index).keys())
            step2 = "Delete the alias {index} for "
        else:
            step2 = "Delete index {index}"
        message = ("Performing an in-place reindex in three steps:\n"
                   "1. Reindex {index} to {new_index}\n"
                   "2. " + step2 + "\n"
                   "3. Alias {new_index} as {index}")
        self._print(message.format(index=index, new_index=new_index))

        if not self._ask("Proceed?"):
            self._print("Aborting.")
            return

        # Do a normal reindex to the chosen new index
        self.reindex(index, new_index)

        # Delete the old index and create an alias for the new index instead.
        if index_is_alias:
            # Remove the alias.
            self._print("Deleting alias {index}.".format(index=index))
            conn.indices.delete_alias(name=index, index='_all')
        else:
            # Delete the index.
            self._print("Deleting old index {index}.".format(index=index))
            conn.indices.delete(index)
        self._print("Creating alias {index} to point to {new_index}.".format(index=index, new_index=new_index))
        conn.indices.put_alias(name=index, index=new_index)


    def put_mappings(self, index):
        conn = self.conn
        for model in self.es_models:
            mapping = model.get_mapping()
            # Apply mapping
            if hasattr(model, '__model__'):
                conn.indices.put_mapping(index=index,
                                         doc_type=model.__type__,
                                         body=mapping)
