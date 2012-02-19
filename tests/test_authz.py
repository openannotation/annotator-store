from annotator.authz import authorize

class TestAuthorization(object):

    def test_authorize_empty(self):
        # An annotation with no permissions field is private
        ann = {}
        assert not authorize(ann, 'read')
        assert not authorize(ann, 'read', 'bob')
        assert not authorize(ann, 'read', 'bob', 'consumerkey')

    def test_authorize_null_consumer(self):
        # An annotation with no consumer set is private
        ann = {'permissions': {'read': ['bob']}}
        assert not authorize(ann, 'read')
        assert not authorize(ann, 'read', 'bob')
        assert not authorize(ann, 'read', 'bob', 'consumerkey')

    def test_authorize_basic(self):
        # Annotation with consumer and permissions fields is actionable as
        # per the permissions spec
        ann = {
            'consumer': 'consumerkey',
            'permissions': {'read': ['bob']}
        }

        assert not authorize(ann, 'read')
        assert not authorize(ann, 'read', 'bob')
        assert authorize(ann, 'read', 'bob', 'consumerkey')
        assert not authorize(ann, 'read', 'alice', 'consumerkey')

        assert not authorize(ann, 'update')
        assert not authorize(ann, 'update', 'bob', 'consumerkey')

    def test_authorize_world(self):
        # Annotation (even without consumer key) is actionable if the action
        # list includes the special string 'group:__world__'
        ann = {
            'permissions': {'read': ['group:__world__']}
        }
        assert authorize(ann, 'read')
        assert authorize(ann, 'read', 'bob')
        assert authorize(ann, 'read', 'bob', 'consumerkey')

    def test_authorize_authenticated(self):
        # Annotation (even without consumer key) is actionable if the action
        # list includes the special string 'group:__authenticated__' and the user
        # is authenticated (i.e. a user and consumer tuple is provided)
        ann = {
            'permissions': {'read': ['group:__authenticated__']}
        }
        assert not authorize(ann, 'read')
        assert not authorize(ann, 'read', 'bob')
        assert authorize(ann, 'read', 'bob', 'consumerkey')

    def test_authorize_consumer(self):
        # Annotation (WITH consumer key) is actionable if the action
        # list includes the special string 'group:__consumer__' and the user
        # is authenticated to the same consumer as that of the annotation
        ann = {
            'permissions': {'read': ['group:__consumer__']}
        }
        assert not authorize(ann, 'read')
        assert not authorize(ann, 'read', 'bob')
        assert not authorize(ann, 'read', 'bob', 'consumerkey')
        ann = {
            'consumer': 'consumerkey',
            'permissions': {'read': ['group:__consumer__']}
        }
        assert not authorize(ann, 'read')
        assert not authorize(ann, 'read', 'bob')
        assert authorize(ann, 'read', 'alice', 'consumerkey')
        assert authorize(ann, 'read', 'bob', 'consumerkey')
        assert not authorize(ann, 'read', 'bob', 'adifferentconsumerkey')
        assert not authorize(ann, 'read', 'group:__consumer__', 'adifferentconsumerkey')

    def test_authorize_owner(self):
        # The annotation-owning user can do anything ('user' is a string)
        ann = {
            'consumer': 'consumerkey',
            'user': 'bob',
            'permissions': {'read': ['alice', 'charlie']}
        }
        assert authorize(ann, 'read', 'bob', 'consumerkey')
        assert not authorize(ann, 'read', 'bob', 'adifferentconsumer')
        assert not authorize(ann, 'read', 'sally', 'consumerkey')

    def test_authorize_read_annotation_user_dict(self):
        # The annotation-owning user can do anything ('user' is an object)
        ann = {
            'consumer': 'consumerkey',
            'user': {'id': 'bob'},
            'permissions': {'read': ['alice', 'charlie']}
        }
        assert authorize(ann, 'read', 'bob', 'consumerkey')
        assert not authorize(ann, 'read', 'bob', 'adifferentconsumer')
        assert not authorize(ann, 'read', 'sally', 'consumerkey')


