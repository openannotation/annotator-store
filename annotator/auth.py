import datetime
import json

import iso8601
import jwt

DEFAULT_TTL = 86400

class Consumer(object):
    def __init__(self, key):
        self.key = key

class User(object):
    def __init__(self, id, consumer, is_admin):
        self.id = id
        self.consumer = consumer
        self.is_admin = is_admin

    @classmethod
    def from_token(cls, token):
        return cls(
            token['userId'],
            Consumer(token['consumerKey']),
            token.get('admin', False)
        )

class Authenticator(object):
    """
    A wrapper around the low-level encode_token() and decode_token() that is
    backend inspecific, and swallows all possible exceptions thrown by badly-
    formatted, invalid, or malicious tokens.
    """

    def __init__(self, consumer_fetcher):
        """
        Arguments:
        consumer_fetcher -- a function which takes a consumer key and returns an object
                            with 'key', 'secret', and 'ttl' attributes
        """
        self.consumer_fetcher = consumer_fetcher

    def request_user(self, request):
        """
        Retrieve the user object associated with the current request.

        Arguments:
        request -- a Flask Request object

        Returns: a user object
        """
        token = self._decode_request_token(request)

        if token:
            try:
                return User.from_token(token)
            except KeyError:
                return None
        else:
            return None

    def _decode_request_token(self, request):
        """
        Retrieve any request token from the passed request, verify its
        authenticity and validity, and return the parsed contents of the token
        if and only if all such checks pass.

        Arguments:
        request -- a Flask Request object
        """

        token = request.headers.get('x-annotator-auth-token')
        if token is None:
            return False

        try:
            unsafe_token = decode_token(token, verify=False)
        except TokenInvalid: # catch junk tokens
            return False

        key = unsafe_token.get('consumerKey')
        if not key:
            return False

        consumer = self.consumer_fetcher(key)
        if not consumer:
            return False

        try:
            return decode_token(token, secret=consumer.secret, ttl=consumer.ttl)
        except TokenInvalid: # catch inauthentic or expired tokens
            return False

class TokenInvalid(Exception):
    pass

# Main auth routines
def encode_token(token, secret):
    token.update({'issuedAt': _now().isoformat()})
    return jwt.encode(token, secret)

def decode_token(token, secret='', ttl=DEFAULT_TTL, verify=True):
    try:
        token = jwt.decode(token, secret, verify=verify)
    except jwt.DecodeError:
        import sys
        exc_class, exc, tb = sys.exc_info()
        new_exc = TokenInvalid("error decoding JSON Web Token: %s" % exc or exc_class)
        raise new_exc.__class__, new_exc, tb

    if verify:
        issue_time = token.get('issuedAt')
        if issue_time is None:
            raise TokenInvalid("'issuedAt' is missing from token")

        issue_time = iso8601.parse_date(issue_time)
        expiry_time = issue_time + datetime.timedelta(seconds=ttl)

        if issue_time > _now():
            raise TokenInvalid("token is not yet valid")
        if expiry_time < _now():
            raise TokenInvalid("token has expired")

    return token

def _now():
    return datetime.datetime.now(iso8601.iso8601.UTC).replace(microsecond=0)
