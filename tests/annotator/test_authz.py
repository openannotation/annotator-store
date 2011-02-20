import json
from nose.tools import assert_raises

from annotator.model import authorize
from annotator.model.couch import Annotation
from annotator.model.couch import rebuild_db, init_model, Metadata


class TestAuthorization():
    testdb = 'annotator-test'

    def setup(self):
        config = {
            'COUCHDB_HOST': 'http://localhost:5984',
            'COUCHDB_DATABASE': self.testdb
            }
        init_model(config)

    def teardown(self):
        del Metadata.SERVER[self.testdb]

    def test_authorise_read_nouser(self):
        ann = Annotation()
        assert authorize(ann, 'read')
        assert authorize(ann, 'read', 'bob')

    def test_authorise_read_user(self):
        ann = Annotation(user='bob')
        assert authorize(ann, 'read', 'bob')
        assert authorize(ann, 'read', 'alice')

    def test_authorise_update_nouser(self):
        ann = Annotation()
        assert authorize(ann, 'update')
        assert authorize(ann, 'update', 'bob')

    def test_authorise_update_user(self):
        ann = Annotation(user='bob')
        assert authorize(ann, 'update', 'bob')
        assert not authorize(ann, 'update', 'alice')

    def test_authorise_delete_nouser(self):
        ann = Annotation()
        assert authorize(ann, 'delete')
        assert authorize(ann, 'delete', 'bob')

    def test_authorise_delete_user(self):
        ann = Annotation(user='bob')
        assert authorize(ann, 'delete', 'bob')
        assert not authorize(ann, 'delete', 'alice')

