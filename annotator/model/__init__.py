from .couch import Annotation
from .couch import Account
# TODO: remove asap (here just for backwards compat)
Consumer = None


def authorize(annotation, action, user=None):
    # If self.user is None, all actions are allowed
    if not annotation.user:
        return True

    # Otherwise, everyone can read and only the same user can
    # do update/delete
    if action is 'read':
        return True
    else:
        return user == annotation.user

def check_password(email, password):
    from werkzeug import generate_password_hash, check_password_hash
    # self.pwdhash = generate_password_hash(password)
    # TODO: make this work!
    account = Account.get_by_email(email)
    return check_password_hash(account.pwdhash, password)

