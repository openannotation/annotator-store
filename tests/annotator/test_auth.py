import hashlib
import datetime

from werkzeug import Headers

import annotator.model as model
import annotator.auth as auth
from annotator.model.couch import rebuild_db, init_model, Metadata

class MockRequest():
    def __init__(self, headers):
        self.headers = headers

def iso8601(t):
    if t == 'now':
        t = datetime.datetime.now()
    elif t == 'future':
        t = datetime.datetime.now() + datetime.timedelta(seconds=300)
    return t.strftime("%Y-%m-%dT%H:%M:%S")

def make_token(key, user_id, issue_time):
    consumer = model.Consumer.get(key)
    token = hashlib.sha256(consumer.secret + user_id + issue_time).hexdigest()
    return token

def make_request(key, user_id, issue_time):
    return MockRequest(Headers([
        ('x-annotator-consumer-key', key),
        ('x-annotator-auth-token', make_token(key, user_id, issue_time)),
        ('x-annotator-auth-token-issue-time', issue_time),
        ('x-annotator-user-id', user_id)
    ]))


testdb = 'annotator-test'
def setup():
    config = {
        'COUCHDB_HOST': 'http://localhost:5984',
        'COUCHDB_DATABASE': testdb
        }
    init_model(config)
    c = model.Consumer(key='Consumer', secret='ConsumerSecret', ttl=300)
    c.save()

def teardown(self):
    del Metadata.SERVER[testdb]


class TestAuth():
    def test_verify_token(self):
        issue_time = iso8601('future')
        tok = make_token('Consumer', 'alice', issue_time)
        assert auth.verify_token(tok, 'Consumer', 'alice', issue_time), "token should have been verified"

    def test_reject_inauthentic_token(self):
        issue_time = iso8601('future')
        tok = make_token('Consumer', 'alice', issue_time)
        assert not auth.verify_token(tok, 'Consumer', 'bob', issue_time), "token was inauthentic, should have been rejected"

    def test_reject_expired_token(self):
        issue_time = iso8601(datetime.datetime.now() - datetime.timedelta(seconds=301))
        tok = make_token('Consumer', 'alice', issue_time)
        assert not auth.verify_token(tok, 'Consumer', 'bob', issue_time), "token had expired, should have been rejected"

    def test_verify_request(self):
        issue_time = iso8601('future')
        request = make_request('Consumer', 'alice', issue_time)
        assert auth.verify_request(request), "request should have been verified"

    def test_reject_request_missing_headers(self):
        issue_time = iso8601('future')
        request = make_request('Consumer', 'alice', issue_time)
        del request.headers['x-annotator-consumer-key']
        assert not auth.verify_request(request), "request missing consumer key should have been rejected"

    def test_verify_request_mixedcase_headers(self):
        issue_time = iso8601('future')
        request = make_request('Consumer', 'alice', issue_time)
        request.headers['X-Annotator-Consumer-Key'] = request.headers['x-annotator-consumer-key']
        assert auth.verify_request(request), "request with mixed-case headers should have been verified"

    def test_get_request_userid(self):
        issue_time = iso8601('future')
        request = make_request('Consumer', 'bob', issue_time)
        assert auth.get_request_userid(request) == 'bob', "didn't extract user id from headers"
