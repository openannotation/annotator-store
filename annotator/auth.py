import datetime
import itsdangerous
import json

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

    def verify_request(self, request):
        token = request.headers.get(HEADER_PREFIX + 'auth-token')

        if not token:
            return False

        unsafe_token = _unsafe_parse_token(token)
        key = unsafe_token.get('consumerKey')
        if not key:
            return False

        consumer = self.consumer_fetcher(key)
        return verify_token(consumer, token)

    def request_credentials(self, request):
        token = self.verify_request(request)

        if not token:
            return None, None
        else:
            return token.get('consumerKey'), token.get('userId')

# Main auth routines
def generate_token(consumer, token=None):
    s = _get_serializer(consumer.key, consumer.secret)
    signer = s.make_signer()

    token = token if token is not None else {}
    token.update({
        'consumerKey': consumer.key,
        'authTokenIssueTime': signer.timestamp_to_datetime(signer.get_timestamp()).isoformat() + 'Z',
        'authTokenTTL': consumer.ttl
    })
    return s.dumps(token)

def verify_token(consumer, token):
    s = _get_serializer(consumer.key, consumer.secret)
    try:
        return s.loads(token, max_age=consumer.ttl)
    except itsdangerous.BadSignature:
        return False

def _get_serializer(key, secret):
    return itsdangerous.TimedSerializer(secret_key=secret, salt="annotator:authToken:{0}".format(key))

def _unsafe_parse_token(token):
    return json.loads(token.rsplit('.', 2)[0])
