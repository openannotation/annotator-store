# Annotator Store

This is a backend store for the [Annotator][1].

## Getting going

You'll need a recent version of [Python][2] (>=2.6) and
[ElasticSearch][3] (>=1.0.0) installed.

[1]: http://okfnlabs.org/annotator
[2]: http://python.org
[3]: http://elasticsearch.org

The quickest way to get going requires the `pip` and `virtualenv` tools
(`easy_install virtualenv` will get them both). Run the following in
the repository root:

    virtualenv pyenv
    source pyenv/bin/activate
    pip install -e .
    cp annotator.cfg.example annotator.cfg
    python run.py

You should see something like:

    * Running on http://127.0.0.1:5000/
    * Restarting with reloader...

If you wish to customize the configuration of the Annotator Store, make your
changes to `annotator.cfg` or dive into `run.py`.

## Store API

The Store API is designed to be compatible with the [Annotator][1]. The
annotation store, a JSON-speaking REST API, will be mounted at `/api` by
default. See the [Annotator documentation][4] for details.

[4]: https://github.com/okfn/annotator/wiki/Storage

## Running tests

We use `nosetests` to run tests. You can just `pip install nosetests mock`,
ensure ElasticSearch is running, and then:

    $ nosetests
    ....................................................
    ----------------------------------------------------------------------
    Ran 52 tests in 3.233s

    OK

Alternatively (and preferably), you should install [Tox][5], and then run
`tox`. This will run the tests against multiple versions of Python (if you
have them installed).

[5]: http://tox.testrun.org/

Please [open an issue](annotator-store/issues) if you find that the tests
don't all pass on your machine, making sure to include the output of `pip
freeze`.
