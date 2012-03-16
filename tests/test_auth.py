import datetime
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
    obj = obj or {}
    obj.update({'consumerKey': consumer.key})
    return MockRequest(Headers([
        ('x-annotator-auth-token', auth.encode_token(obj, consumer.secret))
    ]))

class TestAuthBasics(object):
    def setup(self):
        self.now = auth._now()

        self.time_patcher = patch('annotator.auth._now')
        self.time = self.time_patcher.start()
        self.time.return_value = self.now

    def time_travel(self, **kwargs):
        self.time.return_value = self.now + datetime.timedelta(**kwargs)

    def teardown(self):
        self.time_patcher.stop()

    def test_decode_token(self):
        tok = auth.encode_token({}, 'secret')
        assert auth.decode_token(tok, 'secret'), "token should have been successfully decoded"

    def test_reject_inauthentic_token(self):
        tok = auth.encode_token({'userId': 'alice'}, 'secret')
        tok += 'extrajunk'
        assert_raises(auth.TokenInvalid, auth.decode_token, tok, 'secret')

    def test_reject_notyetvalid_token(self):
        tok = auth.encode_token({}, 'secret')
        self.time_travel(minutes=-1)
        assert_raises(auth.TokenInvalid, auth.decode_token, tok, 'secret')

    def test_reject_expired_token(self):
        tok = auth.encode_token({}, 'secret')
        self.time_travel(seconds=310)
        assert_raises(auth.TokenInvalid, auth.decode_token, tok, 'secret', ttl=300)

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

    def test_request_junk_token(self):
        request = MockRequest(Headers([
            ('x-annotator-auth-token', 'foo.bar.baz')
        ]))
        assert_false(self.auth.verify_request(request))

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
        request.headers['x-annotator-auth-token'] += 'LookMaIAmAHacker'
        assert_equal(self.auth.request_credentials(request), (None, None))
