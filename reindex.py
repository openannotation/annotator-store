import sys
import argparse

from elasticsearch import Elasticsearch

from annotator.reindexer import Reindexer

description = """
Reindex an elasticsearch index.

If old_index and new_index are given the same value, a new name will be
generated for new_index, the old_index will be deleted, and the newly created
index will be aliased to old_index, as to pretend an in-place reindexing. If
old_index was an alias itself, it will be reassigned to target the new index,
and its old target will remain untouched.

WARNING: Documents that are created while reindexing may be lost!
"""

def main(argv):
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('host', help = "Elasticsearch server, host[:port]")
    argparser.add_argument('old_index', help = "Index to read from")
    argparser.add_argument('new_index', help = "Index to write to")
    args = argparser.parse_args()

    host = args.host
    old_index = args.old_index
    new_index = args.new_index

    conn = Elasticsearch([host])

    reindexer = Reindexer(conn, interactive=True)
    reindexer.reindex(old_index, new_index)


if __name__ == '__main__':
    main(sys.argv)
