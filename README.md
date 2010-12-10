# Annotator Store

This is a backend store for the [Annotator][ann].

## Getting going

You'll need a recent version of [python][1] (>=2.6). This code relies on the [`flask`][2] and [`elixir`][3] libraries.

The quickest way to get going assumes you have the `pip` and `virtualenv` tools installed (protip: `easy_install virtualenv` will get them both). Run the following in the repository root:

    pip -E pyenv -r requirements
    source pyenv/bin/activate
    python run.py

You should see something like:

    * Running on http://127.0.0.1:5000/
    * Restarting with reloader...

The annotation store, a JSON-speaking REST API, will be mounted at `http://localhost:5000/store/annotations`. You can test this by running:

    $ curl -i http://localhost:5000/store/annotations
    HTTP/1.0 200 OK
    Content-Type: application/json
    Access-Control-Allow-Origin: *
    Access-Control-Expose-Headers: Location
    Access-Control-Allow-Methods: GET, POST, PUT, DELETE
    Access-Control-Max-Age: 86400
    Content-Length: 2
    Server: Werkzeug/0.6.2 Python/2.6.1
    Date: Fri, 10 Dec 2010 11:44:33 GMT

    []

The "[]" at the end indicates the empty list for your annotations. There are no annotations currently in the store. See the [Annotator repository][ann] for details on getting an annotator talking to this backend.

[ann]: http://nickstenning.github.com/annotator
[1]: http://python.org
[2]: http://flask.pocoo.org
[3]: http://elixir.ematia.de

## Running tests

Running `pip -E pyenv -r requirements` or similar, as described above, should have installed `nose` for you. In the virtualenv, you should be able to run the tests as follows:

    $ nosetests
    .....................
    ----------------------------------------------------------------------
    Ran 21 tests in 0.502s

    OK

Please [open an issue](issues) if you find that the tests don't all pass on your machine, making sure to include the output of `pip freeze`.