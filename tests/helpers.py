class MockConsumer(object):
    def __init__(self, key='annotateit'):
        self.key = key
        self.secret = 'top-secret'
        self.ttl = 86400

class MockUser(object):
    def __init__(self, username='alice'):
        self.username = username

class MockAuthenticator(object):
    def request_credentials(self, request):
        return MockConsumer().key, MockUser().username

def mock_authorizer(*args, **kwargs):
    return True
