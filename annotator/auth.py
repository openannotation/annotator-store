import datetime
import hashlib

import iso8601

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

# Main auth routines

def generate_token(key, user_id):
    from annotator.model import Consumer
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
    from annotator.model import Consumer
    consumer = Consumer.fetch(key)

    if consumer is None:
        return False # invalid account key

    computed_token = hashlib.sha256(consumer.secret + user_id + issue_time).hexdigest()

    if computed_token != token:
        return False # Token inauthentic: computed hash doesn't match.

    validity = iso8601.parse_date(issue_time)
    expiry = validity + datetime.timedelta(seconds=consumer.ttl)

    if validity > datetime.datetime.now(UTC):
        return False # Token not yet valid

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

def get_request_user_id(request):
    if HEADER_PREFIX + 'user-id' in request.headers:
        return request.headers[HEADER_PREFIX + 'user-id']
    else:
        return None

def get_request_consumer_key(request):
    if HEADER_PREFIX + 'consumer-key' in request.headers:
        return request.headers[HEADER_PREFIX + 'consumer-key']
    else:
        return None

def headers_for_token(token):
    return {
        HEADER_PREFIX + 'consumer-key': token['consumerKey'],
        HEADER_PREFIX + 'auth-token': token['authToken'],
        HEADER_PREFIX + 'auth-token-issue-time': token['authTokenIssueTime'],
        HEADER_PREFIX + 'auth-token-ttl': token['authTokenTTL'],
        HEADER_PREFIX + 'user-id': token['userId']
    }
