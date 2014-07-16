import os
from flask import Flask, g, request

from annotator import auth, authz, annotation, document, elasticsearch, store
from annotator.store import es
from .helpers import MockUser, MockConsumer


here = os.path.dirname(__file__)

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile(os.path.join(here, 'test.cfg'))

    es.host = app.config['ELASTICSEARCH_HOST']
    es.index = app.config['ELASTICSEARCH_INDEX']
    es.authorization_enabled = app.config['AUTHZ_ON']

    @app.before_request
    def before_request():
        g.auth = auth.Authenticator(MockConsumer)
        g.authorize = authz.authorize

    app.register_blueprint(store.store, url_prefix='/api')

    return app


class TestCase(object):
    @classmethod
    def setup_class(cls):
        cls.app = create_app()
        annotation.Annotation.drop_all(es)
        document.Document.drop_all(es)

    def setup(self):
        annotation.Annotation.create_all(es)
        document.Document.create_all(es)
        es.conn.cluster.health(wait_for_status='yellow')
        self.cli = self.app.test_client()

    def teardown(self):
        annotation.Annotation.drop_all(es)
        document.Document.drop_all(es)
