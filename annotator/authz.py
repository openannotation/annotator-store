# There are 2 basic authorization scenarios:
#
# 1) Public request: no user/consumer provided
#
# 2) Registered request: user/consumer known and authenticated
#
# In scenario 1, we allow the action if and only if the permissions field for
# that action contains the magic value 'group:__world__'
#
# In scenario 2, we allow the action if ANY of the following conditions are
# satisfied:
#
# a) the permissions field for the specified action contains the magic value
#    'group:__world__'
#
# b) the user and consumer match those of the annotation (i.e. the authenticated
#    user is the owner of the annotation)
#
# c) the permissions field contains the magic value 'group:__authenticated__'
#
# d) the consumer matches that of the annotation and the permissions field for the
#    specified action contains the magic value 'group:__consumer__'
#
# e) the consumer matches that of the annotation and the user is listed in the
#    permissions field for the specified action
#

GROUP_WORLD = 'group:__world__'
GROUP_AUTHENTICATED = 'group:__authenticated__'
GROUP_CONSUMER = 'group:__consumer__'

def authorize(annotation, action, user=None, consumer=None):
    permissions = annotation.get('permissions', {})
    action_field = permissions.get(action, [])

    if not (user and consumer): # Scenario 1, as described above
        return GROUP_WORLD in action_field

    else: # Scenario 2, as described above
        ann_user, ann_consumer = _annotation_owner(annotation)

        if GROUP_WORLD in action_field:
            return True
        elif (user, consumer) == (ann_user, ann_consumer):
            return True
        elif GROUP_AUTHENTICATED in action_field:
            return True
        elif consumer == ann_consumer and GROUP_CONSUMER in action_field:
            return True
        elif consumer == ann_consumer and user in action_field:
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
