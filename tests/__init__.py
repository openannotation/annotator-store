import os
from flask import Flask, g, request

from annotator import es, auth, authz, annotation, document, \
                      elasticsearch_analyzers, store

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
        es.drop_all()

    def setup(self):
        es.create_all(models=[annotation.Annotation, document.Document],
                         analysis_settings=elasticsearch_analyzers.ANALYSIS)
        es.conn.cluster.health(wait_for_status='yellow')
        self.cli = self.app.test_client()

    def teardown(self):
        es.drop_all()
