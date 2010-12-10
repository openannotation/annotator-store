import datetime
import hashlib

import iso8601

__all__ = ["consumers", "verify_token", "Consumer"]

# Hard-code this for the moment. It can go into the database later.
consumers = {
    'testConsumer': {
        'secret': 'FKs78jfYVT93S0vU+vTTCHgT48l1XzhxeW79hWglN2+pfCJsMr80aaXv5CZY7pvRswqouUGqRy8a',
        'ttl': 300
    }
}

# Yoinked from python docs
ZERO = datetime.timedelta(0)
class Utc(datetime.tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO
UTC = Utc()

def verify_token(token, key, userId, issueTime):
    consumer = Consumer(key)
    computedToken = hashlib.sha256(consumer.secret + userId + issueTime).hexdigest()

    if computedToken != token:
        return False # Token inauthentic: computed hash doesn't match.

    expiry = iso8601.parse_date(issueTime) + datetime.timedelta(seconds=consumer.ttl)

    if expiry < datetime.datetime.now(UTC):
        return False # Token expired: issueTime + ttl > now

    return True

class Consumer():
    def __init__(self, key):
        self.data = consumers[key]

    @property
    def secret(self):
        return self.data['secret']

    @property
    def ttl(self):
        return self.data['ttl']