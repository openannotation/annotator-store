class ACTION(object):
    CREATE = u'create'
    READ = u'read'
    UPDATE = u'update'
    DELETE = u'delete'
    ADMIN = u'admin'

def authorize(annotation, action, user=None):
    permissions = annotation.permissions
    authorized_list = permissions.get(action, [])
    # no permissions or empty list indicates anyone can do that action
    if not authorized_list:
        return True
    else:
        return user in authorized_list

