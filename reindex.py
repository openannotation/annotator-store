#!/usr/bin/env python
import sys

from elasticsearch import Elasticsearch, helpers

from annotator.annotation import Annotation
from annotator.document import Document

ES_MODELS = Annotation, Document

# NOTE: Documents that are created while reindexing may be lost in the process!

def reindex(conn, old_index, new_alias=None, new_index=None, delete_old=False):
    """Migrate documents from an index to a new index+alias

       Create new index, reindex contents of old index into new index, and
       create an alias for the new index. The idea is that the new index name
       should be irrelevant, and the alias is to be used to access it, in order
       to simplify future migrations.

       Arguments:
       old_index -- Name of the currently used index.
       new_alias -- Name to be used afterwards. Defaults to equal old_index.
       new_index -- Real name for the new index, default is arbitrary.
       delete_old -- Delete the old index. Must be True if new_alias==old_index
                     and old_index is not an alias itself.
    """
    if new_alias is None:
        new_alias = old_index
    if new_index is None:
        # Find an unused name
        new_index = new_alias + '_real'
        # If it already exists, append a number to it.
        suffix_number = 0
        while conn.indices.exists(new_index) is True:
            suffix_number += 1
            if suffix_number >= 10:
                # Something's probably wrong (we may be in an infinite loop?)
                raise RuntimeError("Desired index names are occupied, please clean up your old indices!")
            new_index = '%s_real%d' % (new_alias, suffix_number)

    if old_index == new_index:
        raise ValueError

    # Create the new index
    conn.indices.create(new_index)

    # Apply the new settings and mappings
    put_mappings(conn, new_index)

    # Do the actual reindexing.
    helpers.reindex(conn, old_index, new_index)

    # Delete the old index if requested.
    if delete_old:
        conn.indices.delete(old_index)

    # (Re)Assign the alias
    if conn.indices.exists_alias(new_alias):
        conn.indices.delete_alias(new_alias)
    conn.indices.put_alias(name=new_alias, index=new_index)


def put_mappings(conn, index):
    for model in ES_MODELS:
        mapping = model._get_mapping()
        # Apply custom settings
        if hasattr(model, '__settings__'):
            conn.indices.put_settings(index=cls.es.index,
                                      body=model.__settings__)

        # Apply mapping
        if hasattr(model, '__model__'):
            conn.indices.put_mapping(index=index,
                                     doc_type=model.__type__,
                                     body=mapping)

def main(argv):
    conn = Elasticsearch() # TODO host settings

    old_index = argv[1]
    reindex(conn, old_index, delete_old=True) # TODO ask permission to delete

if __name__ == '__main__':
    main(sys.argv)
