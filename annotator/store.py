from flask import Flask, Blueprint, Response
from flask import abort, json, redirect, request, url_for, g

from .model import Annotation
from .authz import authorize
from . import auth

__all__ = ["store"]

store = Blueprint('store', __name__)

# We define our own jsonify rather than using flask.jsonify because we wish
# to jsonify arbitrary objects (e.g. index returns a list) rather than kwargs.
def jsonify(obj, *args, **kwargs):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return Response(res, mimetype='application/json', *args, **kwargs)

def get_current_userid():
    return auth.get_request_userid(request)

@store.before_request
def before_request():
    g.consumer_key = request.headers.get('x-annotator-consumer-key')
    g.user_id = request.headers.get('x-annotator-user-id')

    if not auth.verify_request(request):
        return jsonify("Cannot authorise request. Perhaps you didn't send the x-annotator headers?", status=401)

@store.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin']   = '*'
    response.headers['Access-Control-Allow-Headers']  = 'X-Requested-With, Content-Type, X-Annotator-Consumer-Key, X-Annotator-User-Id, X-Annotator-Auth-Token-Issue-Time, X-Annotator-Auth-Token-TTL, X-Annotator-Auth-Token'
    response.headers['Access-Control-Expose-Headers'] = 'Location'
    response.headers['Access-Control-Allow-Methods']  = 'GET, POST, PUT, DELETE'
    response.headers['Access-Control-Max-Age']        = '86400'

    return response

# ROOT
@store.route('/')
def root():
    return jsonify("Annotation store API")

# INDEX
@store.route('/annotations')
def index():
    annotations = [anno for anno in Annotation.search() if authorize(anno, 'read', get_current_userid())]
    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    if request.json:
        annotation = Annotation(request.json)

        if g.consumer_key:
            annotation['consumer'] = g.consumer_key
        if g.user_id:
            annotation['user'] = g.user_id

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
        updated = Annotation(request.json)
        if 'permissions' in updated and updated.get('permissions') != annotation.get('permissions', {}):
            if not authorize(annotation, 'admin', get_current_userid()):
                return jsonify('Could not authorise request (permissions change). No update performed', status=401)
        updated.save()
        return jsonify(updated)
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

# Search
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

