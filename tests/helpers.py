class MockConsumer(object):
    def __init__(self, key='annotateit'):
        self.key = key
        self.secret = 'top-secret'
        self.ttl = 86400

    def __nonzero__(self):
        return not not self.key

class MockUser(object):
    def __init__(self, username='alice'):
        self.username = username

    def __nonzero__(self):
        return not not self.username

class MockAuthenticator(object):
    def verify_token(self, *args, **kwargs):
        return True

    def verify_request(self, *args, **kwargs):
        return True

    def generate_token(self, *args, **kwargs):
        return {
            'consumerKey': MockConsumer().key,
            'authToken': 'null',
            'authTokenIssueTime': '2012-01-01T00:00:00Z',
            'authTokenTTL': 86400,
            'userId': MockUser().username
        }

def mock_authorizer(*args, **kwargs):
    return True
