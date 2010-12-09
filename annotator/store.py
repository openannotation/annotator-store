from flask import Flask, Module
from flask import abort, current_app, g, json, redirect, request, url_for

store = Module(__name__)
annotations = {}

def _next_id():
    if len(annotations) is 0:
        return 0
    else:
        return max(annotations.keys()) + 1

def jsonify(obj):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return current_app.response_class(res, mimetype='application/json')

def unjsonify(str):
    return json.loads(str)

# Store routing:

@store.route('')
def index():
    return jsonify(annotations.values())

@store.route('', methods=['POST'])
def create_annotation():
    if 'json' in request.form:
        id = _next_id()
        annotations[id] = unjsonify(request.form['json'])
        annotations[id][u'id'] = id
        return redirect(url_for('read_annotation', id=id), 303)
    else:
        return jsonify('No parameters given. Annotation not created.'), 400

@store.route('/<int:id>')
def read_annotation(id):
    if id in annotations:
        return jsonify(annotations[id])
    else:
        return jsonify('Annotation not found.'), 404

@store.route('/<int:id>', methods=['PUT'])
def update_annotation(id):
    if id in annotations:
        if 'json' in request.form:
            annotation = unjsonify(request.form['json'])
            annotations[id].update(annotation)
        return jsonify(annotations[id])
    else:
        return jsonify('Annotation not found. No update performed.'), 404

@store.route('/<int:id>', methods=['DELETE'])
def delete_annotation(id):
    if id in annotations:
        del annotations[id]
        return None, 204
    else:
        return jsonify('Annotation not found. No delete performed.'), 404

