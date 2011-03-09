import datetime
import hashlib

import iso8601

from .model import Account

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

def verify_token(token, key, userId, expiryTime=''):
    account = Account.get(key)

    if account is None:
        return False # invalid account key

    computedToken = hashlib.sha256(account.secret + userId + expiryTime).hexdigest()

    if computedToken != token:
        return False # Token inauthentic: computed hash doesn't match.

    if expiryTime:
        expiry = iso8601.parse_date(expiryTime)
        if expiry < datetime.datetime.now(UTC):
            return False

    return True

def verify_request(request):
    pre = HEADER_PREFIX

    required = ['auth-token', 'account-id', 'user-id']
    headers  = [pre + key for key in required]

    rh = request.headers

    # False if not all the required headers have been provided
    if not set(headers) <= set([key.lower() for key in rh.keys()]):
        return False

    ttl_header = pre+'auth-token-valid-until'
    if ttl_header in rh:
        result = verify_token( *[rh[h] for h in headers + [ttl_header]] )
    else:
        result = verify_token( *[rh[h] for h in headers] )

    return result

def get_request_userid(request):
    if HEADER_PREFIX + 'user-id' in request.headers:
        return request.headers[HEADER_PREFIX + 'user-id']
    else:
        return None

