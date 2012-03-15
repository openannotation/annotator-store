import hashlib
import time

from nose.tools import *
from mock import Mock, patch

from werkzeug import Headers

from annotator import auth

class MockRequest():
    def __init__(self, headers):
        self.headers = headers

class MockConsumer(Mock):
    key    = 'Consumer'
    secret = 'ConsumerSecret'
    ttl    = 300

def make_request(consumer, obj=None):
    return MockRequest(Headers([
        ('x-annotator-auth-token', auth.generate_token(consumer, obj))
    ]))

class TestAuthBasics(object):
    def setup(self):
        self.consumer = MockConsumer()
        self.now = time.time()

        self.time_patcher = patch('itsdangerous.time.time')
        self.time = self.time_patcher.start()
        self.time.return_value = self.now

    def teardown(self):
        self.time_patcher.stop()

    def test_verify_token(self):
        tok = auth.generate_token(self.consumer)
        assert auth.verify_token(self.consumer, tok), "token should have been verified"

    def test_reject_inauthentic_token(self):
        tok = auth.generate_token(self.consumer, {'userId': 'alice'})
        tok = tok.replace('alice', 'bob')
        assert not auth.verify_token(self.consumer, tok), "token was inauthentic, should have been rejected"

    def test_reject_expired_token(self):
        tok = auth.generate_token(self.consumer)
        self.time.return_value = self.now + 301
        assert not auth.verify_token(self.consumer, tok), "token had expired, should have been rejected"

class TestAuthenticator(object):
    def setup(self):
        self.consumer = MockConsumer()
        fetcher = lambda x: self.consumer
        self.auth = auth.Authenticator(fetcher)

    def test_verify_request(self):
        request = make_request(self.consumer)
        assert self.auth.verify_request(request), "request should have been verified"

    def test_reject_request_missing_headers(self):
        request = make_request(self.consumer)
        del request.headers['x-annotator-auth-token']
        assert not self.auth.verify_request(request), "request missing auth token should have been rejected"

    def test_request_credentials(self):
        request = make_request(self.consumer)
        assert_equal(self.auth.request_credentials(request), ('Consumer', None))

    def test_request_credentials_user(self):
        request = make_request(self.consumer, {'userId': 'alice'})
        assert_equal(self.auth.request_credentials(request), ('Consumer', 'alice'))

    def test_request_credentials_missing(self):
        request = make_request(self.consumer)
        del request.headers['x-annotator-auth-token']
        assert_equal(self.auth.request_credentials(request), (None, None))

    def test_request_credentials_invalid(self):
        request = make_request(self.consumer)
        request.headers['x-annotator-auth-token'] = request.headers['x-annotator-auth-token'].replace('Consumer', 'LookMaIAmAHacker')
        assert_equal(self.auth.request_credentials(request), (None, None))


