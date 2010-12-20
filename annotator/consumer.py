from flask import Module, jsonify

from . import auth

consumer = Module(__name__)

@consumer.route('/token')
def generate_token():
    tokenData = auth.generate_token('testConsumer', 'alice')
    return jsonify(**tokenData)
