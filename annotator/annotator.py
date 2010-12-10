from flask import Flask
from flask import g, json, request

from .store import store

app = Flask(__name__)

@store.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin']   = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Location'
    response.headers['Access-Control-Allow-Methods']  = 'GET, POST, PUT, DELETE'
    response.headers['Access-Control-Max-Age']        = '86400'
    return response

def setup_app():
    app.register_module(store, url_prefix=app.config['MOUNTPOINT'])
