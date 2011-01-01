from flask import Module, jsonify

from . import auth

consumer = Module(__name__)

consumer.test_consumer_key = None
consumer.test_consumer_user = None

@consumer.route('/token')
def generate_token():
    if not consumer.test_consumer_key:
        raise Exception, "No test_consumer_key specified."

    if not consumer.test_consumer_user:
        raise Exception, "No test_consumer_user specified."

    tokenData = auth.generate_token(
        consumer.test_consumer_key,
        consumer.test_consumer_user
    )

    return jsonify(**tokenData)
