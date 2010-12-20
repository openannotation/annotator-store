from flask import Flask, Module
from flask import abort, json, redirect, request, url_for

from .model import Annotation, Range, session
from . import auth

__all__ = ["app", "store", "setup_app"]

app = Flask('annotator')
store = Module(__name__)

def setup_app():
    app.register_module(store, url_prefix=app.config['MOUNTPOINT'])

# We define our own jsonify rather than using flask.jsonify because we wish
# to jsonify arbitrary objects (e.g. index returns a list) rather than kwargs.
def jsonify(obj, *args, **kwargs):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return app.response_class(res, mimetype='application/json', *args, **kwargs)

def unjsonify(str):
    return json.loads(str)

@store.before_request
def before_request():
    if app.config['AUTH_ON'] and not auth.verify_request(request):
        return jsonify("Cannot authorise request. Perhaps you didn't send the x-annotator headers?", status=401)


@store.after_request
def after_request(response):
    if response.status_code < 300:
        response.headers['Access-Control-Allow-Origin']   = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Location'
        response.headers['Access-Control-Allow-Methods']  = 'GET, POST, PUT, DELETE'
        response.headers['Access-Control-Max-Age']        = '86400'

    return response

# INDEX
@store.route('/annotations')
def index():
    annotations = [a.to_dict() for a in Annotation.query.all()]
    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    if request.json:
        annotation = Annotation()
        annotation.from_dict(request.json)

        session.commit()

        return jsonify(annotation.to_dict())
    else:
        return jsonify('No parameters given. Annotation not created.', status=400)

# READ
@store.route('/annotations/<int:id>')
def read_annotation(id):
    annotation = Annotation.get(id)

    if annotation:
        return jsonify(annotation.to_dict())
    else:
        return jsonify('Annotation not found.', status=404)

# UPDATE
@store.route('/annotations/<int:id>', methods=['PUT'])
def update_annotation(id):
    annotation = Annotation.get(id)

    if annotation:
        if request.json:
            annotation.from_dict(request.json)

            session.commit()

        return jsonify(annotation.to_dict())
    else:
        return jsonify('Annotation not found. No update performed.', status=404)

# DELETE
@store.route('/annotations/<int:id>', methods=['DELETE'])
def delete_annotation(id):
    annotation = Annotation.get(id)

    if annotation:
        annotation.delete()
        session.commit()

        return None, 204
    else:
        return jsonify('Annotation not found. No delete performed.', status=404)

# Search
@store.route('/search')
def search_annotations():
    # TODO: actually do some searching.
    annotations = [a.to_dict() for a in Annotation.query.all()]
    return jsonify({'results': annotations})