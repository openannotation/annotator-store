import os
from flask import Flask, g, request

from annotator import es, auth, authz, annotation, store

from .helpers import MockUser, MockConsumer

here = os.path.dirname(__file__)

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile(os.path.join(here, 'test.cfg'))

    es.init_app(app)

    @app.before_request
    def before_request():
        g.user = MockUser(request.headers.get(auth.HEADER_PREFIX + 'user-id'))
        g.consumer = MockConsumer(request.headers.get(auth.HEADER_PREFIX + 'consumer-key'))

        g.auth = auth.Authenticator(MockConsumer)
        g.authorize = authz.authorize

    app.register_blueprint(store.store, url_prefix='/api')

    return app

class TestCase(object):
    @classmethod
    def setup_class(cls):
        cls.app = create_app()
        with cls.app.test_request_context():
            annotation.Annotation.drop_all()

    def setup(self):
        with self.app.test_request_context():
            annotation.Annotation.create_all()
        self.cli = self.app.test_client()

    def teardown(self):
        with self.app.test_request_context():
            annotation.Annotation.drop_all()
