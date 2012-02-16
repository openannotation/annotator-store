import pyes

import annotator

def setup():
    app = annotator.create_app()
    try:
        annotator.drop_all(app)
    except pyes.exceptions.ElasticSearchException:
        pass


class TestCase(object):
    def setup(self):
        self.app = annotator.create_app()
        annotator.create_all(self.app)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

        self.db = self.app.extensions['sqlalchemy'].db
        self.es = self.app.extensions['pyes']

    def teardown(self):
        self.ctx.pop()
        annotator.drop_all(self.app)
