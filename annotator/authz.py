PUBLIC_ACTIONS = ['read']

# There are 2 basic authorization scenarios:
#
# 1) Public request: no user provided
#
# 2) Registered request: user known and (later) authenticated
#
# In scenario 1, we allow the action if BOTH of the following criteria are
# satisfied, namely a) the annotation has a null or empty permissions field
# for that action, AND b) the action is in the PUBLIC_ACTIONS list.
#
# In scenario 2, we allow the action if ANY of the following criteria are
# satisfied, namely a) the annotation has a null or empty permissions field
# for that action, OR b) the user is listed in the permissions field for that
# action, OR c) the user is the owner of the annotation, as listed in the
# annotation 'user' field, which should either be a string or a dict with an
# 'id' key.

def authorize(annotation, action, user=None):
    permissions = annotation.get('permissions', {})
    action_field = permissions.get(action, [])

    if not user: # Scenario 1, as described above
        return (not action_field) and (action in PUBLIC_ACTIONS)

    else: # Scenario 2, as described above
        if user == _annotation_owner_id(annotation):
            return True
        if not action_field:
            return True
        else:
            return user in action_field

def _annotation_owner_id(annotation):
    if 'user' not in annotation:
        return None
    try:
        return annotation['user'].get('id', None)
    except AttributeError:
        return annotation['user']
