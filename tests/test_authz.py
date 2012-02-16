from annotator.authz import authorize

class TestAuthorization(object):

    def test_authorize_read_nouser(self):
        ann = dict()
        assert authorize(ann, 'read')
        assert authorize(ann, 'read', 'bob')

    def test_authorize_read_user(self):
        ann = dict(permissions={'read': ['bob']})
        assert authorize(ann, 'read', 'bob')
        assert not authorize(ann, 'read', 'alice')

    def test_authorize_update_nouser(self):
        ann = dict()
        assert not authorize(ann, 'update')
        assert authorize(ann, 'update', 'bob')

    def test_authorize_update_user(self):
        ann = dict(permissions={'update': ['bob']})
        assert authorize(ann, 'update', 'bob')
        assert not authorize(ann, 'update', 'alice')

    def test_authorize_delete_nouser(self):
        ann = dict()
        assert not authorize(ann, 'delete')
        assert authorize(ann, 'delete', 'bob')

    def test_authorize_delete_user(self):
        ann = dict(permissions={'delete': ['bob']})
        assert authorize(ann, 'delete', 'bob')
        assert not authorize(ann, 'delete', 'alice')

    def test_authorize_admin_nouser(self):
        ann = dict()
        assert not authorize(ann, 'admin')
        assert authorize(ann, 'admin', 'bob')

    def test_authorize_admin_user(self):
        ann = dict(permissions={'admin': ['bob']})
        assert authorize(ann, 'admin', 'bob')
        assert not authorize(ann, 'admin', 'alice')

