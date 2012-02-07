def authorize(annotation, action, user=None):
    permissions = annotation.get('permissions', {})
    authorized_list = permissions.get(action, [])
    # no permissions or empty list indicates anyone can do that action
    if not authorized_list:
        return True
    else:
        return user in authorized_list

