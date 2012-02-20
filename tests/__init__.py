import os

import pyes
from flask import Flask, g, request, current_app

from annotator import auth, authz, annotation, store

from .helpers import MockUser, MockConsumer

here = os.path.dirname(__file__)

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile(os.path.join(here, 'test.cfg'))

    @app.before_request
    def before_request():
        g.esconn = pyes.ES(current_app.config['ELASTICSEARCH_HOST'])
        g.Annotation = annotation.make_model(g.esconn, index=current_app.config['ELASTICSEARCH_INDEX'])

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
        cls.conn = pyes.ES(cls.app.config['ELASTICSEARCH_HOST'])
        cls.Annotation = annotation.make_model(cls.conn, index=cls.app.config['ELASTICSEARCH_INDEX'])
        cls.Annotation.drop_all()

    def setup(self):
        self.Annotation.create_all()
        self.cli = self.app.test_client()

    def teardown(self):
        self.Annotation.drop_all()
