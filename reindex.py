import sys
import argparse

from elasticsearch import Elasticsearch

from annotator.reindexer import Reindexer

description = """
Reindex an elasticsearch index.

WARNING: Documents that are created while reindexing may be lost!
"""

def main(argv):
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('old_index', help="Index to read from")
    argparser.add_argument('new_index', help="Index to write to")
    argparser.add_argument('--host', help="Elasticsearch server, host[:port]")
    argparser.add_argument('--alias', help="Alias for the new index")
    args = argparser.parse_args()

    host = args.host
    old_index = args.old_index
    new_index = args.new_index
    alias = args.alias

    if host:
        conn = Elasticsearch([host])
    else:
        conn = Elasticsearch()


    reindexer = Reindexer(conn, interactive=True)

    reindexer.reindex(old_index, new_index)

    if alias:
        reindexer.alias(new_index, alias)

if __name__ == '__main__':
    main(sys.argv)
