Changelog
=========

All notable changes to this project will be documented in this file. This
project endeavours to adhere to `Semantic Versioning`_.

.. _Semantic Versioning: http://semver.org/

0.14.2 2015-07-17
-----------------

-  FIXED: `Annotation.search` no longer mutates the passed query.

-  FIXED/BREAKING CHANGE: `Document.get_by_uri()` no longer returns a list for
   empty resultsets, instead returning `None`.

0.14.1 2015-03-05
-----------------
-  FIXED: Document plugin doesn't drop links without a type. The annotator
   client generates a typeless link from the document href. (#116)

-  ADDED: the search endpoint now supports 'before' and 'after query parameters,
   which can be used to return annotations created between a specific time
   period.

0.14 - 2015-02-13
-----------------

-  ADDED: the search endpoint now supports 'sort' and 'order' query parameters,
   which can be used to control the sort order of the returned results.

-  FIXED: previously only one document was returned when looking for equivalent
   documents (#110). Now the Document model tracks all discovered equivalent
   documents and keeps each document object up-to-date with them all.

-  BREAKING CHANGE: Document.get_all_by_uris() no longer exists. Use
   Document.get_by_uri() which should return a single document containing all
   equivalent URIs. (You may wish to update your index by fetching all documents
   and resaving them.)

-  FIXED: the search_raw endpoint no longer throws an exception when the
   'fields' parameter is provided.

0.13.2 - 2014-12-03
-------------------

-  Avoid a confusing error about reindexing when annotator is used as a
   library and not a standalone application (#107).

0.13.1 - 2014-12-03
-------------------

-  Reindexer can run even when target exists.

0.13.0 - 2014-12-02
-------------------

-  Slight changes to reindex.py to ease subclassing it.

0.12.0 - 2014-10-06
-------------------

-  A tool for migrating/reindexing elasticsearch (reindex.py) was added (#103).
-  The store returns more appropriate HTTP response codes (#96).
-  Dropped support for ElasticSearch versions before 1.0.0 (#92).
-  The default search query has been changed from a term-filtered "match all" to
   a set of "match queries", resulting in more liberal interpretations of
   queries (#89).
-  The default elasticsearch analyzer for annotation fields has been changed to
   "keyword" in order to provide more consistent case-sensitivity behaviours
   (#73, #88).
-  Made Flask an optional dependency: it is now possible to use the persistence
   components of the project without needing Flask (#76).
-  Python 3 compatibility (#72).


0.11.2 - 2014-07-25
-------------------

-  SECURITY: Fixed bug that allowed authenticated users to overwrite annotations
   on which they did not have permissions (#82).

0.11.1 - 2014-04-09
-------------------

-  Fixed support for using ElasticSearch instances behind HTTP Basic auth

0.11.0 - 2014-04-08
-------------------

-  Add support for ElasticSearch 1.0
-  Create changelog
