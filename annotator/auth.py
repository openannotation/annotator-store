import datetime
import hashlib

import iso8601

from .model import Consumer

__all__ = ["verify_token", "verify_request"]

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

def generate_token(key, user_id):
    consumer = Consumer.fetch(key)

    if consumer is None:
        raise Exception, "Cannot generate token: invalid consumer key specified"

    issue_time = datetime.datetime.now(UTC).isoformat()
    token = hashlib.sha256(consumer.secret + user_id + issue_time).hexdigest()

    return dict(
        consumerKey=key,
        authToken=token,
        authTokenIssueTime=issue_time,
        authTokenTTL=consumer.ttl,
        userId=user_id
    )

def verify_token(token, key, user_id, issue_time):
    consumer = Consumer.fetch(key)

    if consumer is None:
        return False # invalid account key

    computed_token = hashlib.sha256(consumer.secret + user_id + issue_time).hexdigest()

    if computed_token != token:
        return False # Token inauthentic: computed hash doesn't match.

    expiry = iso8601.parse_date(issue_time) + datetime.timedelta(seconds=consumer.ttl)

    if expiry < datetime.datetime.now(UTC):
        return False # Token expired: issue_time + ttl > now

    return True

def verify_request(request):
    required = ['auth-token', 'consumer-key', 'user-id', 'auth-token-issue-time']
    headers  = [HEADER_PREFIX + key for key in required]

    rh = request.headers

    # False if not all the required headers have been provided
    if not set(headers) <= set([key.lower() for key in rh.keys()]):
        return False

    result = verify_token( *[rh[h] for h in headers] )

    return result

def get_request_userid(request):
    if HEADER_PREFIX + 'user-id' in request.headers:
        return request.headers[HEADER_PREFIX + 'user-id']
    else:
        return None

