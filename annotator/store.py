import json

from flask import Blueprint, Response
from flask import g
from flask import request

from annotator.annotation import Annotation

store = Blueprint('store', __name__)

CREATE_FILTER_FIELDS = ('updated', 'created', 'consumer')
UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

# We define our own jsonify rather than using flask.jsonify because we wish
# to jsonify arbitrary objects (e.g. index returns a list) rather than kwargs.
def jsonify(obj, *args, **kwargs):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return Response(res, mimetype='application/json', *args, **kwargs)

@store.after_request
def after_request(response):
    ac = 'Access-Control-'

    response.headers[ac + 'Allow-Origin']      = request.headers.get('origin', '*')
    response.headers[ac + 'Allow-Credentials'] = 'true'
    response.headers[ac + 'Expose-Headers']    = 'Location, Content-Type, Content-Length'

    if request.method == 'OPTIONS':
        response.headers[ac + 'Allow-Headers']  = 'X-Requested-With, Content-Type, Content-Length, X-Annotator-Consumer-Key, X-Annotator-User-Id, X-Annotator-Auth-Token-Issue-Time, X-Annotator-Auth-Token-TTL, X-Annotator-Auth-Token'
        response.headers[ac + 'Allow-Methods']  = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers[ac + 'Max-Age']        = '86400'

    return response

# ROOT
@store.route('/')
def root():
    return jsonify("Annotator Store API")

# INDEX
@store.route('/annotations')
def index():
    consumer, user = g.auth.request_credentials(request)
    annotations = Annotation.search(_user_id=user, _consumer_key=consumer)
    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    consumer, user = g.auth.request_credentials(request)

    # Only registered users can create annotations
    if not (consumer and user):
        return _failed_auth_response()

    if request.json:
        annotation = Annotation(_filter_input(request.json, CREATE_FILTER_FIELDS))

        annotation['consumer'] = consumer
        if _get_annotation_user(annotation) != user:
            annotation['user'] = user

        annotation.save()

        return jsonify(annotation)
    else:
        return jsonify('No JSON payload sent. Annotation not created.', status=400)

# READ
@store.route('/annotations/<id>')
def read_annotation(id):
    annotation = Annotation.fetch(id)
    if not annotation:
        return jsonify('Annotation not found!', status=404)

    failure = _check_action(annotation, 'read')
    if failure:
        return failure

    return jsonify(annotation)

# UPDATE
@store.route('/annotations/<id>', methods=['POST', 'PUT'])
def update_annotation(id):
    annotation = Annotation.fetch(id)
    if not annotation:
        return jsonify('Annotation not found! No update performed.', status=404)

    failure = _check_action(annotation, 'update')
    if failure:
        return failure

    if request.json:
        updated = _filter_input(request.json, UPDATE_FILTER_FIELDS)
        updated['id'] = id # use id from URL, regardless of what arrives in JSON payload

        if 'permissions' in updated and updated['permissions'] != annotation.get('permissions', {}):
            failure = _check_action(annotation, 'admin', message='permissions update')
            if failure:
                return failure

        annotation.update(updated)
        annotation.save()

    return jsonify(annotation)

# DELETE
@store.route('/annotations/<id>', methods=['DELETE'])
def delete_annotation(id):
    annotation = Annotation.fetch(id)

    if not annotation:
        return jsonify('Annotation not found. No delete performed.', status=404)

    failure = _check_action(annotation, 'delete')
    if failure:
        return failure

    annotation.delete()
    return None, 204

# SEARCH
@store.route('/search')
def search_annotations():
    kwargs = dict(request.args.items())

    consumer, user = g.auth.request_credentials(request)

    kwargs['_consumer_key'] = consumer
    kwargs['_user_id'] = user

    if 'offset' in kwargs:
        kwargs['offset'] = _quiet_int(kwargs['offset'])
    if 'limit' in kwargs:
        kwargs['limit'] = _quiet_int(kwargs['limit'], 20)

    results = Annotation.search(**kwargs)
    total = Annotation.count(**kwargs)
    return jsonify({
        'total': total,
        'rows': results
    })

def _filter_input(obj, fields):
    for field in fields:
        obj.pop(field, None)

    return obj

def _get_annotation_user(ann):
    """Returns the best guess at this annotation's owner user id"""
    user = ann.get('user')

    if not user:
        return None

    try:
        return user.get('id', None)
    except AttributeError:
        return user

def _check_action(annotation, action, message=''):
    consumer, user = g.auth.request_credentials(request)

    if not g.authorize(annotation, action, user, consumer):
        return _failed_authz_response(message)

def _failed_authz_response(msg=''):
    return jsonify("Cannot authorize request{0}. Perhaps you're not logged in as "
                   "a user with appropriate permissions on this annotation?".format(' (' + msg + ')' if msg else ''),
                   status=401)

def _failed_auth_response():
    return jsonify("Cannot authenticate request. Perhaps you didn't send the "
                   "X-Annotator-* headers?",
                   status=401)

def _quiet_int(obj, default=0):
    try:
        return int(obj)
    except ValueError:
        return default
