import hashlib
import datetime

import annotator.auth as auth

fixture = {
    'testConsumer': {
        'secret': 'testConsumerSecret',
        'ttl': 300
    }
}

def iso8601(t):
    t = datetime.datetime.now() if t == 'now' else t
    return t.strftime("%Y-%m-%dT%H:%M:%S")

def make_token(consumerKey, userId, issueTime):
    c = auth.Consumer(key=consumerKey)
    return hashlib.sha256(c.secret + userId + issueTime).hexdigest()

def setup():
    auth.consumers = fixture

class TestAuth():
    def test_verify_token(self):
        issueTime = iso8601('now')
        tok = make_token('testConsumer', 'alice', issueTime)
        assert auth.verify_token(tok, 'testConsumer', 'alice', issueTime), "token should have been verified"

    def test_reject_inauthentic_token(self):
        issueTime = iso8601('now')
        tok = make_token('testConsumer', 'alice', issueTime)
        assert not auth.verify_token(tok, 'testConsumer', 'bob', issueTime), "token was inauthentic, should have been rejected"

    def test_reject_expired_token(self):
        issueTime = iso8601(datetime.datetime.now() - datetime.timedelta(seconds=301))
        tok = make_token('testConsumer', 'alice', issueTime)
        assert not auth.verify_token(tok, 'testConsumer', 'bob', issueTime), "token had expired, should have been rejected"

class TestConsumer():
    def test_consumer_secret(self):
        c = auth.Consumer(key='testConsumer')
        assert c.secret == 'testConsumerSecret'

    def test_consumer_ttl(self):
        c = auth.Consumer(key='testConsumer')
        assert c.ttl == 300
