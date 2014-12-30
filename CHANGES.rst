Next release
============

- Support custom analyzers in Elasticsearch
- Fix bug '_csv_split not found'

0.13.2
======

- Avoid a confusing error about reindexing when annotator is used as a
  library and not a standalone application (#107).

0.13.1
======

- Reindexer can run even when target exists.

0.13
====

- Slight changes to reindex.py to ease subclassing it.

0.12
====

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


0.11.2
======

-  SECURITY: Fixed bug that allowed authenticated users to overwrite annotations
   on which they did not have permissions (#82).

0.11.1
======

-  Fixed support for using ElasticSearch instances behind HTTP Basic auth

0.11.0
======

-  Add support for ElasticSearch 1.0
-  Create changelog
