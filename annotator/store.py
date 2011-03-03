from flask import Flask, Module, Response
from flask import abort, json, redirect, request, url_for

from .model import Annotation, authorize
from . import auth

__all__ = ["store"]

store = Module(__name__)

from flask import current_app 


# We define our own jsonify rather than using flask.jsonify because we wish
# to jsonify arbitrary objects (e.g. index returns a list) rather than kwargs.
def jsonify(obj, *args, **kwargs):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return Response(res, mimetype='application/json', *args, **kwargs)

def unjsonify(str):
    return json.loads(str)

def get_current_userid():
    return auth.get_request_userid(request)

@store.before_request
def before_request():
    if current_app.config['AUTH_ON'] and not request.method == 'GET' and not auth.verify_request(request):
        return jsonify("Cannot authorise request. Perhaps you didn't send the x-annotator headers?", status=401)

@store.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin']   = '*'
    # response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'X-Requested-With, Content-Type, X-Annotator-Account-Id, X-Annotator-User-Id, X-Annotator-Auth-Token-Valid-Until, X-Annotator-Auth-Token'
    response.headers['Access-Control-Expose-Headers'] = 'Location'
    response.headers['Access-Control-Allow-Methods']  = 'GET, POST, PUT, DELETE'
    response.headers['Access-Control-Max-Age']        = '86400'

    return response

# INDEX
@store.route('/annotations')
def index():
    annotations = [row.doc for row in Annotation.search() if authorize(a, 'read', get_current_userid())]
    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    if request.json:
        annotation = Annotation.from_dict(request.json)
        annotation.save()
        return jsonify(annotation.to_dict())
    else:
        return jsonify('No parameters given. Annotation not created.', status=400)

# READ
@store.route('/annotations/<id>')
def read_annotation(id):
    annotation = Annotation.get(id)

    if not annotation:
        return jsonify('Annotation not found.', status=404)

    elif authorize(annotation, 'read', get_current_userid()):
        return jsonify(annotation.to_dict())

    else:
        return jsonify('Could not authorise request. No update performed', status=401)

# UPDATE
@store.route('/annotations/<id>', methods=['PUT'])
def update_annotation(id):
    annotation = Annotation.get(id)

    if not annotation:
        return jsonify('Annotation not found. No update performed.', status=404)

    elif request.json and authorize(annotation, 'update', get_current_userid()):
        annotation = Annotation.from_dict(request.json)
        annotation.save()
        return jsonify(annotation.to_dict())

    else:
        return jsonify('Could not authorise request. No update performed', status=401)

# DELETE
@store.route('/annotations/<id>', methods=['DELETE'])
def delete_annotation(id):
    print id
    annotation = Annotation.get(id)

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
    # TODO: limit results returned to max 200
    results = [ x.to_dict() for x in Annotation.search(**kwargs) ]
    # TODO: a proper count(*) for this query
    total = len(results)
    qrows = {
        'total': total,
        'rows': results,
    }
    return jsonify(qrows)

