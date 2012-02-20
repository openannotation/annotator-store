import hashlib
import datetime

from nose.tools import *

from werkzeug import Headers

from annotator import auth

class MockRequest():
    def __init__(self, headers):
        self.headers = headers

class MockConsumer():
    key = 'Consumer'
    secret = 'ConsumerSecret'
    ttl = 300

def make_issue_time(offset=0):
    t = datetime.datetime.now() + datetime.timedelta(seconds=offset)
    return t.strftime("%Y-%m-%dT%H:%M:%S")

def make_token(consumer, user_id, issue_time):
    token = hashlib.sha256(consumer.secret + user_id + issue_time).hexdigest()
    return token

def make_request(consumer, user_id, issue_time):
    return MockRequest(Headers([
        ('x-annotator-consumer-key', consumer.key),
        ('x-annotator-auth-token', make_token(consumer, user_id, issue_time)),
        ('x-annotator-auth-token-issue-time', issue_time),
        ('x-annotator-user-id', user_id)
    ]))

def test_verify_token():
    issue_time = make_issue_time()
    tok = make_token(MockConsumer, 'alice', issue_time)
    assert auth.verify_token(MockConsumer, tok, 'alice', issue_time), "token should have been verified"

def test_reject_inauthentic_token():
    issue_time = make_issue_time()
    tok = make_token(MockConsumer, 'alice', issue_time)
    assert not auth.verify_token(MockConsumer, tok, 'bob', issue_time), "token was inauthentic, should have been rejected"

def test_reject_invalid_token():
    issue_time = make_issue_time(300)
    tok = make_token(MockConsumer, 'alice', issue_time)
    assert not auth.verify_token(MockConsumer, tok, 'alice', issue_time), "token not yet valid, should have been rejected"

def test_reject_expired_token():
    issue_time = make_issue_time(-301)
    tok = make_token(MockConsumer, 'alice', issue_time)
    assert not auth.verify_token(MockConsumer, tok, 'bob', issue_time), "token had expired, should have been rejected"

def test_headers_for_token():
    headers = auth.headers_for_token({
        'consumerKey': 'consumerFoo',
        'authToken': 'abc',
        'authTokenIssueTime': 'now',
        'authTokenTTL': 300,
        'userId': 'userBar'
    })
    assert_equal(headers, {
        'x-annotator-consumer-key': 'consumerFoo',
        'x-annotator-auth-token': 'abc',
        'x-annotator-auth-token-issue-time': 'now',
        'x-annotator-auth-token-ttl': 300,
        'x-annotator-user-id': 'userBar'
    })

class TestAuthenticator(object):
    def setup(self):
        fetcher = lambda x: MockConsumer()
        self.auth = auth.Authenticator(fetcher)

    def test_generate_token(self):
        issue_time = make_issue_time()
        tok = self.auth.generate_token('Consumer', 'alice')
        assert tok

    def test_verify_token(self):
        issue_time = make_issue_time()
        tok = make_token(MockConsumer, 'alice', issue_time)
        assert self.auth.verify_token('Consumer', tok, 'alice', issue_time), "token should have been verified"

    def test_verify_request(self):
        issue_time = make_issue_time()
        request = make_request(MockConsumer, 'alice', issue_time)
        assert self.auth.verify_request(request), "request should have been verified"

    def test_reject_request_missing_headers(self):
        issue_time = make_issue_time()
        request = make_request(MockConsumer, 'alice', issue_time)
        del request.headers['x-annotator-consumer-key']
        assert not self.auth.verify_request(request), "request missing consumer key should have been rejected"

    def test_verify_request_mixedcase_headers(self):
        issue_time = make_issue_time()
        request = make_request(MockConsumer, 'alice', issue_time)
        request.headers['X-Annotator-Consumer-Key'] = request.headers['x-annotator-consumer-key']
        assert self.auth.verify_request(request), "request with mixed-case headers should have been verified"
