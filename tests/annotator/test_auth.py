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

def make_token(account_id, userId, expiryTime):
    c = model.Account.get(account_id)
    return hashlib.sha256(c.secret + userId + expiryTime).hexdigest()

def make_request(account_id, userId, expiryTime):
    return MockRequest(Headers([
        ('x-annotator-account-id', account_id),
        ('x-annotator-auth-token', make_token(account_id, userId, expiryTime)),
        ('x-annotator-auth-token-valid-until', expiryTime),
        ('x-annotator-user-id', userId)
    ]))


testdb = 'annotator-test'
def setup():
    config = {
        'COUCHDB_HOST': 'http://localhost:5984',
        'COUCHDB_DATABASE': testdb
        }
    init_model(config)
    c = model.Account(id='testAccount', secret='testAccountSecret')
    c.save()

def teardown(self):
    del Metadata.SERVER[testdb]


class TestAuth():
    def test_verify_token(self):
        expiryTime = iso8601('future')
        tok = make_token('testAccount', 'alice', expiryTime)
        assert auth.verify_token(tok, 'testAccount', 'alice', expiryTime), "token should have been verified"

    def test_reject_inauthentic_token(self):
        expiryTime = iso8601('future')
        tok = make_token('testAccount', 'alice', expiryTime)
        assert not auth.verify_token(tok, 'testAccount', 'bob', expiryTime), "token was inauthentic, should have been rejected"

    def test_reject_expired_token(self):
        expiryTime = iso8601(datetime.datetime.now() - datetime.timedelta(seconds=301))
        tok = make_token('testAccount', 'alice', expiryTime)
        assert not auth.verify_token(tok, 'testAccount', 'bob', expiryTime), "token had expired, should have been rejected"

    def test_verify_request(self):
        expiryTime = iso8601('future')
        request = make_request('testAccount', 'alice', expiryTime)
        assert auth.verify_request(request), "request should have been verified"

    def test_reject_request_missing_headers(self):
        expiryTime = iso8601('future')
        request = make_request('testAccount', 'alice', expiryTime)
        del request.headers['x-annotator-account-id']
        assert not auth.verify_request(request), "request missing account_id should have been rejected"

    def test_verify_request_mixedcase_headers(self):
        expiryTime = iso8601('future')
        request = make_request('testAccount', 'alice', expiryTime)
        request.headers['X-Annotator-Account-Key'] = request.headers['x-annotator-account-id']
        assert auth.verify_request(request), "request with mixed-case headers should have been verified"

    def test_get_request_userid(self):
        expiryTime = iso8601('future')
        request = make_request('testAccount', 'bob', expiryTime)
        assert auth.get_request_userid(request) == 'bob', "didn't extract userid from headers"
