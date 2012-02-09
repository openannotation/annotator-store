from flask import Flask, Blueprint, current_app
from flask import abort, redirect, request, g, url_for

from annotator.model import Annotation
from annotator.util import jsonify
from annotator import auth, authz

__all__ = ["store"]

store = Blueprint('store', __name__)

def current_user_id():
    return auth.get_request_userid(request)

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
    return jsonify({
        'name': 'Annotator Store API',
        'version': '2.0.0'
    })

# INDEX
@store.route('/annotations')
def index():
    uid = current_user_id()

    if uid:
        if not auth.verify_request(request):
            return _failed_auth_response()
        annotations = Annotation.search(_user_id=uid)
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
        annotation = Annotation(_filter_input(request.json))

        annotation['consumer'] = request.headers[auth.HEADER_PREFIX + 'consumer-key']
        annotation['user'] = request.headers[auth.HEADER_PREFIX + 'user-id']

        annotation.save()

        return redirect(url_for('.read_annotation', id=annotation.id), 303)
    else:
        return jsonify('No JSON payload sent. Annotation not created.', status=400)

# READ
@store.route('/annotations/<id>')
def read_annotation(id):
    annotation = Annotation.fetch(id)
    if not annotation:
        return jsonify('Annotation not found!', status=404)

    failure = _check_action(annotation, 'read', current_user_id())
    if failure:
        return failure

    return jsonify(annotation)

# UPDATE
@store.route('/annotations/<id>', methods=['PUT'])
def update_annotation(id):
    annotation = Annotation.fetch(id)
    if not annotation:
        return jsonify('Annotation not found! No update performed.', status=404)

    failure = _check_action(annotation, 'update', current_user_id())
    if failure:
        return failure

    if request.json:
        updated = _filter_input(request.json)
        updated['id'] = id # use id from URL, regardless of what arrives in JSON payload

        if 'permissions' in updated and updated['permissions'] != annotation.get('permissions', {}):
            if not authz.authorize(annotation, 'admin', current_user_id()):
                return _failed_authz_response('permissions update')

        annotation.update(updated)
        annotation.save()

    return redirect(url_for('.read_annotation', id=annotation.id), 303)

# DELETE
@store.route('/annotations/<id>', methods=['DELETE'])
def delete_annotation(id):
    annotation = Annotation.fetch(id)

    if not annotation:
        return jsonify('Annotation not found. No delete performed.', status=404)

    failure = _check_action(annotation, 'delete', current_user_id())
    if failure:
        return failure

    annotation.delete()
    return None, 204

# SEARCH
@store.route('/search')
def search_annotations():
    kwargs = dict(request.args.items())
    uid = current_user_id()

    if uid:
        if not auth.verify_request(request):
            return _failed_auth_response()

        kwargs['_user_id'] = uid

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

def _filter_input(obj):
    for field in ['updated', 'created', 'user', 'consumer']:
        if field in obj:
            del obj[field]

    return obj

def _check_action(annotation, action, uid):
    if not authz.authorize(annotation, action, uid):
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
