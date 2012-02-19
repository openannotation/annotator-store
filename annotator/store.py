from flask import Flask, Blueprint, current_app
from flask import abort, redirect, request, g

from annotator.model import Annotation
from annotator.util import jsonify
from annotator import auth, authz

__all__ = ["store"]

store = Blueprint('store', __name__)

CREATE_FILTER_FIELDS = ('updated', 'created', 'consumer')
UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

def current_user():
    return (auth.get_request_user_id(request), auth.get_request_consumer_key(request))

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
    uid, ckey = current_user()

    if ckey and uid:
        if not auth.verify_request(request):
            return _failed_auth_response()

        annotations = Annotation.search(_user_id=uid, _consumer_key=ckey)
    else:
        annotations = Annotation.search()

    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    # Only registered users can create annotations
    if not auth.verify_request(request):
        return _failed_auth_response()

    if request.json:
        annotation = Annotation(_filter_input(request.json, CREATE_FILTER_FIELDS))

        uid, ckey = current_user()
        annotation['consumer'] = ckey
        if _get_annotation_user(annotation) != uid:
            annotation['user'] = uid

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

    failure = _check_action(annotation, 'read', *current_user())
    if failure:
        return failure

    return jsonify(annotation)

# UPDATE
@store.route('/annotations/<id>', methods=['POST', 'PUT'])
def update_annotation(id):
    annotation = Annotation.fetch(id)
    if not annotation:
        return jsonify('Annotation not found! No update performed.', status=404)

    failure = _check_action(annotation, 'update', *current_user())
    if failure:
        return failure

    if request.json:
        updated = _filter_input(request.json, UPDATE_FILTER_FIELDS)
        updated['id'] = id # use id from URL, regardless of what arrives in JSON payload

        if 'permissions' in updated and updated['permissions'] != annotation.get('permissions', {}):
            if not authz.authorize(annotation, 'admin', *current_user()):
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

    failure = _check_action(annotation, 'delete', *current_user())
    if failure:
        return failure

    annotation.delete()
    return None, 204

# SEARCH
@store.route('/search')
def search_annotations():
    kwargs = dict(request.args.items())
    uid, ckey = current_user()

    if ckey and uid:
        if not auth.verify_request(request):
            return _failed_auth_response()

        kwargs['_consumer_key'] = ckey
        kwargs['_user_id'] = uid
    else:
        # Prevent request forgery
        kwargs.pop('_consumer_key', None)
        kwargs.pop('_user_id', None)

    results = Annotation.search(**kwargs)
    total = Annotation.count(**kwargs)
    return jsonify({
        'total': total,
        'rows': results,
    })

# AUTH TOKEN
@store.route('/token')
def auth_token():
    if g.user:
        return jsonify(auth.generate_token('annotateit', g.user.username))
    else:
        root = current_app.config['ROOT_URL']
        return jsonify('Please go to {0} to log in!'.format(root), status=401)

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

def _check_action(annotation, action, uid, ckey):
    if not authz.authorize(annotation, action, uid, ckey):
        return _failed_authz_response()

    if uid and not auth.verify_request(request):
        return _failed_auth_response()

def _failed_authz_response(msg=''):
    return jsonify("Cannot authorize request{0}. Perhaps you're not logged in as "
                   "a user with appropriate permissions on this annotation?".format(' (' + msg + ')'),
                   status=401)

def _failed_auth_response():
    return jsonify("Cannot authenticate request. Perhaps you didn't send the "
                   "X-Annotator-* headers?",
                   status=401)
