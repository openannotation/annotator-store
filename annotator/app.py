from flask import Flask
from flask import g, json, request

from annotator.store import store

app = Flask('annotator')
mountpoint = '/store/annotations'

@store.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin']   = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Location'
    response.headers['Access-Control-Allow-Methods']  = 'GET, POST, PUT, DELETE'
    response.headers['Access-Control-Max-Age']        = '86400'
    return response

def run():
    app.register_module(store, url_prefix=mountpoint)
    app.debug = True
    app.run()

def test_client():
    app.register_module(store, url_prefix=mountpoint)
    return app.test_client()