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

def authorize(annotation, action, user=None):
    uid = user.id if user else None
    ckey = user.consumer.key if user else None

    # Fail fast if this looks dodgy
    if uid and uid.startswith('group:'):
        return False

    permissions = annotation.get('permissions', {})
    action_field = permissions.get(action, [])

    ann_uid, ann_ckey = _annotation_owner(annotation)

    # Scenario 1
    if GROUP_WORLD in action_field:
        return True

    elif uid and ckey:

        # Scenario 2
        if (uid, ckey) == (ann_uid, ann_ckey):
            return True

        # Scenario 3
        elif GROUP_AUTHENTICATED in action_field:
            return True

        # Scenario 4
        elif ckey == ann_ckey and GROUP_CONSUMER in action_field:
            return True

        # Scenario 5
        elif ckey == ann_ckey and uid in action_field:
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

def permissions_filter(es_query, user=None):
    """ Filter an ElasticSearch query by the permissions of the current user """
    uid = user.id if user else None
    ckey = user.consumer.key if user else None

    # Scenario 1
    perm_f = {'term': {'permissions.read': GROUP_WORLD}}

    if uid and ckey:
        perm_f = {'or': [perm_f]}

        # Scenario 2
        perm_f['or'].append({'and': [{'term': {'consumer': ckey}},
                                     {'or': [{'term': {'user': uid}},
                                             {'term': {'user.id': uid}}]}]})

        # Scenario 3
        perm_f['or'].append({'term': {'permissions.read': GROUP_AUTHENTICATED}})

        # Scenario 4
        perm_f['or'].append({'and': [{'term': {'consumer': ckey}},
                                     {'term': {'permissions.read': GROUP_CONSUMER}}]})

        # Scenario 5
        perm_f['or'].append({'and': [{'term': {'consumer': ckey}},
                                     {'term': {'permissions.read': uid}}]})

    return {'filtered': {'filter': perm_f, 'query': es_query}}
