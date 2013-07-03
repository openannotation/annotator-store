# An action is permitted in any of the following scenarios:
#
# 1) the permissions field for the specified action contains the magic value
#    'group:__world__'
#
# 2) the user and consumer match those of the annotation (i.e. the
#    authenticated user is the owner of the annotation)
#
# 3) a user and consumer are provided and the permissions field contains the
#    magic value 'group:__authenticated__'
#
# 4) the provided consumer matches that of the annotation and the permissions
#    field for the specified action contains the magic value
#    'group:__consumer__'
#
# 5) the consumer matches that of the annotation and the user is listed in the
#    permissions field for the specified action
#
# 6) the consumer matches that of the annotation and the user is an admin

GROUP_WORLD = 'group:__world__'
GROUP_AUTHENTICATED = 'group:__authenticated__'
GROUP_CONSUMER = 'group:__consumer__'


def authorize(annotation, action, user=None):
    action_field = annotation.get('permissions', {}).get(action, [])

    # Scenario 1
    if GROUP_WORLD in action_field:
        return True

    elif user is not None:
        # Fail fast if this looks dodgy
        if user.id.startswith('group:'):
            return False

        ann_uid, ann_ckey = _annotation_owner(annotation)

        # Scenario 2
        if (user.id, user.consumer.key) == (ann_uid, ann_ckey):
            return True

        # Scenario 3
        elif GROUP_AUTHENTICATED in action_field:
            return True

        # Scenario 4
        elif user.consumer.key == ann_ckey and GROUP_CONSUMER in action_field:
            return True

        # Scenario 5
        elif user.consumer.key == ann_ckey and user.id in action_field:
            return True

        # Scenario 6
        elif user.consumer.key == ann_ckey and user.is_admin:
            return True

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


def permissions_filter(user=None):
    """Filter an ElasticSearch query by the permissions of the current user"""

    # Scenario 1
    perm_f = {'term': {'permissions.read': GROUP_WORLD}}

    if user is not None:
        # Fail fast if this looks dodgy
        if user.id.startswith('group:'):
            return False

        perm_f = {'or': [perm_f]}

        # Scenario 2
        perm_f['or'].append(
            {'and': [{'term': {'consumer': user.consumer.key}},
                     {'or': [{'term': {'user': user.id}},
                             {'term': {'user.id': user.id}}]}]})

        # Scenario 3
        perm_f['or'].append(
            {'term': {'permissions.read': GROUP_AUTHENTICATED}})

        # Scenario 4
        perm_f['or'].append(
            {'and': [{'term': {'consumer': user.consumer.key}},
                     {'term': {'permissions.read': GROUP_CONSUMER}}]})

        # Scenario 5
        perm_f['or'].append(
            {'and': [{'term': {'consumer': user.consumer.key}},
                     {'term': {'permissions.read': user.id}}]})

        # Scenario 6
        if user.is_admin:
            perm_f['or'].append({'term': {'consumer': user.consumer.key}})

    return perm_f
