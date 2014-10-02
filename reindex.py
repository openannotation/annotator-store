import sys
import argparse

from elasticsearch import Elasticsearch

from annotator.reindexer import Reindexer

description = """
Reindex an elasticsearch index.

Performs reindexing and/or aliasing of an index.

WARNING: Documents that are created while reindexing may be lost!
"""

def main(argv):
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('host', help="Elasticsearch server, host[:port]")
    argparser.add_argument('--reindex', action='append', nargs=2, metavar=('old_index', 'new_index'),
                           help="Reindex old_index to new_index")
    argparser.add_argument('--alias', action='append', nargs=2, metavar=('index', 'alias'),
                           help="Create an alias for an index")
    args = argparser.parse_args()

    host = args.host
    reindex = args.reindex or []
    alias = args.alias or []

    conn = Elasticsearch([host])

    reindexer = Reindexer(conn, interactive=True)

    for (old_index, new_index) in reindex:
        reindexer.reindex(old_index, new_index)
    for (index, alias) in alias:
        reindexer.alias(index, alias)

if __name__ == '__main__':
    main(sys.argv)
