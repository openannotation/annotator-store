import os
from flask import Flask, g, request

from annotator import es, auth, authz, annotation, store, document

from .helpers import MockUser, MockConsumer

here = os.path.dirname(__file__)


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile(os.path.join(here, 'test.cfg'))

    es.init_app(app)

    @app.before_request
    def before_request():
        g.auth = auth.Authenticator(MockConsumer)
        g.authorize = authz.authorize

    app.register_blueprint(store.store, url_prefix='/api')

    return app


# pyes 0.19.1 has a bug where cluster.health sends the arguments in
# a JSON request body instead of as query parameters. The fix is
# already upstream, but here's a workaround for now. Remove this once
# a new pyes is released and the dependency version is updated in
# annotator-store.
def wait_for_status(conn, level='yellow'):
    params = dict(wait_for_status=level)
    conn._send_request('GET', '/_cluster/health', params=params)


class TestCase(object):
    @classmethod
    def setup_class(cls):
        cls.app = create_app()
        with cls.app.app_context():
            annotation.Annotation.drop_all()
            document.Document.drop_all()

    def setup(self):
        with self.app.app_context():
            annotation.Annotation.create_all()
            document.Document.create_all()
        self.cli = self.app.test_client()
        wait_for_status(es.get_conn(self.app))

    def teardown(self):
        with self.app.app_context():
            annotation.Annotation.drop_all()
            document.Document.drop_all()
