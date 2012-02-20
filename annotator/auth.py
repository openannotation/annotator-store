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

class Authenticator(object):

    def __init__(self, consumer_fetcher):
        self.consumer_fetcher = consumer_fetcher

    def generate_token(self, key, *args):
        consumer = self.consumer_fetcher(key)
        return generate_token(consumer, *args)

    def verify_token(self, key, *args):
        consumer = self.consumer_fetcher(key)
        return verify_token(consumer, *args)

    def verify_request(self, request):
        required = ['consumer-key', 'auth-token', 'user-id', 'auth-token-issue-time']
        headers  = [HEADER_PREFIX + key for key in required]

        rh = request.headers

        # False if not all the required headers have been provided
        if not set(headers) <= set([key.lower() for key in rh.keys()]):
            return False

        result = self.verify_token( *[rh[h] for h in headers] )

        return result

# Main auth routines

def generate_token(consumer, user_id):
    issue_time = datetime.datetime.now(UTC).isoformat()
    token = hashlib.sha256(consumer.secret + user_id + issue_time).hexdigest()

    return dict(
        consumerKey=consumer.key,
        authToken=token,
        authTokenIssueTime=issue_time,
        authTokenTTL=consumer.ttl,
        userId=user_id
    )

def verify_token(consumer, token, user_id, issue_time):
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

def headers_for_token(token):
    return {
        HEADER_PREFIX + 'consumer-key': token['consumerKey'],
        HEADER_PREFIX + 'auth-token': token['authToken'],
        HEADER_PREFIX + 'auth-token-issue-time': token['authTokenIssueTime'],
        HEADER_PREFIX + 'auth-token-ttl': token['authTokenTTL'],
        HEADER_PREFIX + 'user-id': token['userId']
    }
