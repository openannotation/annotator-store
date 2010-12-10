from flask import Flask, Module
from flask import abort, current_app, g, json, redirect, request, url_for

from .model import Annotation, Range, session

store = Module(__name__)

# We define our own jsonify rather than using flask.jsonify because we wish
# to jsonify arbitrary objects (e.g. index returns a list) rather than kwargs.
def jsonify(obj):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return current_app.response_class(res, mimetype='application/json')

def unjsonify(str):
    return json.loads(str)

# INDEX
@store.route('')
def index():
    annotations = [a.to_dict() for a in Annotation.query.all()]
    return jsonify(annotations)

# CREATE
@store.route('', methods=['POST'])
def create_annotation():
    if 'json' in request.form:
        annotation = Annotation()
        data = unjsonify(request.form['json'])
        annotation.from_dict(data)

        session.commit()

        return redirect(url_for('read_annotation', id=annotation.id), 303)
    else:
        return jsonify('No parameters given. Annotation not created.'), 400

# READ
@store.route('/<int:id>')
def read_annotation(id):
    annotation = Annotation.get(id)

    if annotation:
        return jsonify(annotation.to_dict())
    else:
        return jsonify('Annotation not found.'), 404

# UPDATE
@store.route('/<int:id>', methods=['PUT'])
def update_annotation(id):
    annotation = Annotation.get(id)

    if annotation:
        if 'json' in request.form:
            data = unjsonify(request.form['json'])
            annotation.from_dict(data)

            session.commit()

        return jsonify(annotation.to_dict())
    else:
        return jsonify('Annotation not found. No update performed.'), 404

# DELETE
@store.route('/<int:id>', methods=['DELETE'])
def delete_annotation(id):
    annotation = Annotation.get(id)

    if annotation:
        annotation.delete()
        session.commit()

        return None, 204
    else:
        return jsonify('Annotation not found. No delete performed.'), 404
