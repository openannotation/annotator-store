import json

from flask import Flask, Blueprint, Response
from flask import current_app, g
from flask import abort, redirect, request

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
    response.headers[ac + 'Expose-Headers']    = 'Location'

    if request.method == 'OPTIONS':
        response.headers[ac + 'Allow-Headers']  = 'X-Requested-With, Content-Type, X-Annotator-Consumer-Key, X-Annotator-User-Id, X-Annotator-Auth-Token-Issue-Time, X-Annotator-Auth-Token-TTL, X-Annotator-Auth-Token'
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
    if g.consumer and g.user:
        if not g.auth.verify_request(request):
            return _failed_auth_response()

        annotations = Annotation.search(_user_id=g.user.username, _consumer_key=g.consumer.key)
    else:
        annotations = Annotation.search()

    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    # Only registered users can create annotations
    if not g.auth.verify_request(request):
        return _failed_auth_response()

    if request.json:
        annotation = Annotation(_filter_input(request.json, CREATE_FILTER_FIELDS))

        annotation['consumer'] = g.consumer.key
        if _get_annotation_user(annotation) != g.user.username:
            annotation['user'] = g.user.username

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

    failure = _check_action(annotation, 'read', g.user, g.consumer)
    if failure:
        return failure

    return jsonify(annotation)

# UPDATE
@store.route('/annotations/<id>', methods=['POST', 'PUT'])
def update_annotation(id):
    annotation = Annotation.fetch(id)
    if not annotation:
        return jsonify('Annotation not found! No update performed.', status=404)

    failure = _check_action(annotation, 'update', g.user, g.consumer)
    if failure:
        return failure

    if request.json:
        updated = _filter_input(request.json, UPDATE_FILTER_FIELDS)
        updated['id'] = id # use id from URL, regardless of what arrives in JSON payload

        if 'permissions' in updated and updated['permissions'] != annotation.get('permissions', {}):
            if not g.authorize(annotation, 'admin', g.user.username, g.consumer.key):
                return _failed_authz_response('permissions update')

        annotation.update(updated)
        annotation.save()

    return jsonify(annotation)

# DELETE
@store.route('/annotations/<id>', methods=['DELETE'])
def delete_annotation(id):
    annotation = Annotation.fetch(id)

    if not annotation:
        return jsonify('Annotation not found. No delete performed.', status=404)

    failure = _check_action(annotation, 'delete', g.user, g.consumer)
    if failure:
        return failure

    annotation.delete()
    return None, 204

# SEARCH
@store.route('/search')
def search_annotations():
    kwargs = dict(request.args.items())

    if g.user and g.consumer:
        if not g.auth.verify_request(request):
            return _failed_auth_response()

        kwargs['_consumer_key'] = g.consumer.key
        kwargs['_user_id'] = g.user.username
    else:
        # Prevent request forgery
        kwargs.pop('_consumer_key', None)
        kwargs.pop('_user_id', None)

    if 'offset' in kwargs:
        kwargs['offset'] = _quiet_int(kwargs['offset'])
    if 'limit' in kwargs:
        kwargs['limit'] = _quiet_int(kwargs['limit'], 20)

    results = Annotation.search(**kwargs)
    total = Annotation.count(**kwargs)
    return jsonify({
        'total': total,
        'rows': results,
    })

# AUTH TOKEN
@store.route('/token')
def auth_token():
    if g.session_user:
        return jsonify(g.auth.generate_token('annotateit', g.session_user.username))
    else:
        return jsonify('Please go to {0} to log in!'.format(request.host_url), status=401)

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

def _check_action(annotation, action, user, consumer):
    if not user or not consumer or not g.authorize(annotation, action, user.username, consumer.key):
        return _failed_authz_response()

    if user and not g.auth.verify_request(request):
        return _failed_auth_response()

def _failed_authz_response(msg=''):
    return jsonify("Cannot authorize request{0}. Perhaps you're not logged in as "
                   "a user with appropriate permissions on this annotation?".format(' (' + msg + ')'),
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
