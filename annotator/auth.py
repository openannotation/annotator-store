import datetime
import hashlib

import iso8601

from .model import Consumer

__all__ = ["consumers", "generate_token", "verify_token", "verify_request"]

HEADER_PREFIX = 'x-annotator-'

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

def generate_token(key, userId):
    consumer = Consumer.get(key)

    if consumer is None:
        raise Exception, "Cannot generate token: invalid consumer key specified"

    issueTime = datetime.datetime.now(UTC).isoformat()
    token = hashlib.sha256(consumer.secret + userId + issueTime).hexdigest()

    return dict(
        consumerKey=key,
        authToken=token,
        authTokenIssueTime=issueTime,
        authTokenTTL=consumer.ttl,
        userId=userId
    )

def verify_token(token, key, userId, issueTime):
    consumer = Consumer.get(key)

    if consumer is None:
        return False # invalid consumer key

    computedToken = hashlib.sha256(consumer.secret + userId + issueTime).hexdigest()

    if computedToken != token:
        return False # Token inauthentic: computed hash doesn't match.

    expiry = iso8601.parse_date(issueTime) + datetime.timedelta(seconds=consumer.ttl)

    if expiry < datetime.datetime.now(UTC):
        return False # Token expired: issueTime + ttl > now

    return True

def verify_request(request):
    pre = HEADER_PREFIX

    required = ['auth-token', 'consumer-key', 'user-id', 'auth-token-issue-time']
    headers  = [pre + key for key in required]

    rh = request.headers

    # False if not all the required headers have been provided
    if not set(headers) <= set([key.lower() for key in rh.keys()]):
        return False

    result = verify_token( *[rh[h] for h in headers] )

    return result


