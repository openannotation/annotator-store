# An action is permitted in any of the following scenarios:
#
# 1) the permissions field for the specified action contains the magic value
#    'group:__world__'
#
# 2) the user and consumer match those of the annotation (i.e. the authenticated
#    user is the owner of the annotation)
#
# 3) a user and consumer are provided and the permissions field contains the
#    magic value 'group:__authenticated__'
#
# 4) the provided consumer matches that of the annotation and the permissions
#    field for the specified action contains the magic value 'group:__consumer__'
#
# 5) the consumer matches that of the annotation and the user is listed in the
#    permissions field for the specified action
#

GROUP_WORLD = 'group:__world__'
GROUP_AUTHENTICATED = 'group:__authenticated__'
GROUP_CONSUMER = 'group:__consumer__'

def authorize(annotation, action, user=None, consumer=None):
    permissions = annotation.get('permissions', {})
    action_field = permissions.get(action, [])

    ann_user, ann_consumer = _annotation_owner(annotation)

    # Scenario 1
    if GROUP_WORLD in action_field:
        return True

    # Scenario 2
    elif user and consumer and (user, consumer) == (ann_user, ann_consumer):
        return True

    # Scenario 3
    elif user and consumer and GROUP_AUTHENTICATED in action_field:
        return True

    # Scenario 4
    elif consumer and consumer == ann_consumer and GROUP_CONSUMER in action_field:
        return True

    # Scenario 5
    elif consumer and consumer == ann_consumer and user and user in action_field:
        return True

    else:
        return False

def _annotation_owner(annotation):
    user = annotation.get('user')
    consumer = annotation.get('consumer')

    if not user:
        return (user, consumer)

    try:
        return (user.get('id', None), consumer)
    except AttributeError:
        return (user, consumer)
