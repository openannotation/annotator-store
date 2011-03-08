import json
from nose.tools import assert_raises

from annotator.authz import authorize, ACTION
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

    def test_authorize_read_nouser(self):
        ann = Annotation()
        assert authorize(ann, 'read')
        assert authorize(ann, 'read', 'bob')

    def test_authorize_read_user(self):
        ann = Annotation(permissions={ACTION.READ: ['bob']})
        assert authorize(ann, 'read', 'bob')
        assert not authorize(ann, 'read', 'alice')

    def test_authorize_update_nouser(self):
        ann = Annotation()
        assert authorize(ann, 'update')
        assert authorize(ann, 'update', 'bob')

    def test_authorize_update_user(self):
        ann = Annotation(permissions={ACTION.UPDATE: ['bob']})
        assert authorize(ann, 'update', 'bob')
        assert not authorize(ann, 'update', 'alice')

    def test_authorize_delete_nouser(self):
        ann = Annotation()
        assert authorize(ann, 'delete')
        assert authorize(ann, 'delete', 'bob')

    def test_authorize_delete_user(self):
        ann = Annotation(permissions={ACTION.DELETE: ['bob']})
        assert authorize(ann, 'delete', 'bob')
        assert not authorize(ann, 'delete', 'alice')

    def test_authorize_admin_nouser(self):
        ann = Annotation()
        assert authorize(ann, 'admin')
        assert authorize(ann, 'admin', 'bob')

    def test_authorize_admin_user(self):
        ann = Annotation(permissions={ACTION.ADMIN: ['bob']})
        assert authorize(ann, 'admin', 'bob')
        assert not authorize(ann, 'admin', 'alice')

