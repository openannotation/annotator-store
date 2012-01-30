import annotator

def setup():
    annotator.create_app()

class TestCase(object):
    def setup(self):
        annotator.create_all()
        self.ctx = annotator.app.test_request_context()
        self.ctx.push()

    def teardown(self):
        self.ctx.pop()
        annotator.drop_all()
