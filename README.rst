Annotator Store
===============

This is a backend store for `Annotator <http://annotatorjs.org>`__.

Getting going
-------------

You'll need a recent version of `Python <http://python.org>`__ (Python 2 >=2.6
or Python 3 >=3.3) and `ElasticSearch <http://elasticsearch.org>`__ (>=1.0.0)
installed.

The quickest way to get going requires the ``pip`` and ``virtualenv``
tools (``easy_install virtualenv`` will get them both). Run the
following in the repository root::

    virtualenv pyenv
    source pyenv/bin/activate
    pip install -e .
    cp annotator.cfg.example annotator.cfg
    python run.py

You should see something like::

    * Running on http://127.0.0.1:5000/
    * Restarting with reloader...

If you wish to customize the configuration of the Annotator Store, make
your changes to ``annotator.cfg`` or dive into ``run.py``.

Additionally, the ``HOST`` and ``PORT`` environment variables override
the default socket binding of address ``127.0.0.1`` and port ``5000``.

Store API
---------

The Store API is designed to be compatible with the
`Annotator <http://okfnlabs.org/annotator>`__. The annotation store, a
JSON-speaking REST API, will be mounted at ``/api`` by default. See the
`Annotator
documentation <https://github.com/okfn/annotator/wiki/Storage>`__ for
details.

Running tests
-------------

We use ``nosetests`` to run tests. You can just
``pip install nose mock``, ensure ElasticSearch is running, and
then::

    $ nosetests
    ....................................................
    ----------------------------------------------------------------------
    Ran 52 tests in 3.233s

    OK

Alternatively (and preferably), you should install
`Tox <http://tox.testrun.org/>`__, and then run ``tox``. This will run
the tests against multiple versions of Python (if you have them
installed).

Please `open an issue <annotator-store/issues>`__ if you find that the
tests don't all pass on your machine, making sure to include the output
of ``pip freeze``.
