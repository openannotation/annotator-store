from flask import Flask, Blueprint, current_app
from flask import abort, redirect, request, g

from annotator.model import Annotation
from annotator.authz import authorize
from annotator.util import jsonify
from annotator.user import get_current_user
from annotator import auth

__all__ = ["store"]

store = Blueprint('store', __name__)

def get_current_userid():
    return auth.get_request_userid(request)

@store.before_request
def before_request():
    # Don't require authentication headers with OPTIONS request
    if request.method == 'OPTIONS':
        return

    # Don't require authentication headers for auth token request
    # (expecting a session cookie instead)
    if request.endpoint in ['store.root', 'store.auth_token']:
        return

    if not auth.verify_request(request):
        return jsonify("Cannot authorise request. Perhaps you didn't send the x-annotator headers?", status=401)

@store.after_request
def after_request(response):
    ac = 'Access-Control-'

    response.headers[ac + 'Allow-Origin']      = request.headers.get('origin', '*')
    response.headers[ac + 'Allow-Credentials'] = 'true'

    if request.method == 'OPTIONS':
        response.headers[ac + 'Allow-Headers']  = 'X-Requested-With, Content-Type, X-Annotator-Consumer-Key, X-Annotator-User-Id, X-Annotator-Auth-Token-Issue-Time, X-Annotator-Auth-Token-TTL, X-Annotator-Auth-Token'
        response.headers[ac + 'Expose-Headers'] = 'Location'
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
    annotations = [anno for anno in Annotation.search() if authorize(anno, 'read', get_current_userid())]
    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    consumer_key = request.headers.get('x-annotator-consumer-key')
    user_id = request.headers.get('x-annotator-user-id')

    if request.json:
        annotation = Annotation(_filter_input(request.json))

        if consumer_key:
            annotation['consumer'] = consumer_key
        if user_id:
            annotation['user'] = user_id

        annotation.save()
        return jsonify(annotation)
    else:
        return jsonify('No parameters given. Annotation not created.', status=400)

# READ
@store.route('/annotations/<id>')
def read_annotation(id):
    annotation = Annotation.fetch(id)

    if not annotation:
        return jsonify('Annotation not found.', status=404)
    elif authorize(annotation, 'read', get_current_userid()):
        return jsonify(annotation)
    else:
        return jsonify('Could not authorise request. Read not allowed', status=401)

# UPDATE
@store.route('/annotations/<id>', methods=['POST', 'PUT'])
def update_annotation(id):
    annotation = Annotation.fetch(id)

    if not annotation:
        return jsonify('Annotation not found. No update performed.', status=404)

    elif request.json and authorize(annotation, 'update', get_current_userid()):
        updated = _filter_input(request.json)
        updated['id'] = id # use id from URL, regardless of what arrives in payload json

        if 'permissions' in updated and updated.get('permissions') != annotation.get('permissions', {}):
            if not authorize(annotation, 'admin', get_current_userid()):
                return jsonify('Could not authorise request (permissions change). No update performed', status=401)

        annotation.update(updated)
        annotation.save()

        return jsonify(annotation)
    else:
        return jsonify('Could not authorise request. No update performed', status=401)

# DELETE
@store.route('/annotations/<id>', methods=['DELETE'])
def delete_annotation(id):
    annotation = Annotation.fetch(id)

    if not annotation:
        return jsonify('Annotation not found. No delete performed.', status=404)

    elif authorize(annotation, 'delete', get_current_userid()):
        annotation.delete()
        return None, 204

    else:
        return jsonify('Could not authorise request. No update performed', status=401)

# SEARCH
@store.route('/search')
def search_annotations():
    kwargs = dict(request.args.items())
    results = [anno for anno in Annotation.search(**kwargs) if authorize(anno, 'read', get_current_userid())]
    total = Annotation.count(**kwargs)
    qrows = {
        'total': total,
        'rows': results,
    }
    return jsonify(qrows)

# AUTH TOKEN
@store.route('/token')
def auth_token():
    user = get_current_user()

    if user:
        return jsonify(auth.generate_token('annotateit', user.username))
    else:
        root = current_app.config['ROOT_URL']
        return jsonify('Please go to {} to log in!'.format(root), status=401)

def _filter_input(obj):
    for field in ['updated', 'created', 'user', 'consumer']:
        if field in obj:
            del obj[field]

    return obj
