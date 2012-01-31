from flask import Blueprint
from flask import render_template

from annotator.model import Consumer

home = Blueprint('home', __name__)

@home.route('/')
def index():
    return render_template('index.html')
