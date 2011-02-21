from .sqlelixir import Annotation, Consumer, Range


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

