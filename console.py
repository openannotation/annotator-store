from IPython import embed

from flask import request

import annotator
from annotator import auth

app = annotator.create_app()
ctx = app.test_request_context()
ctx.push()

from annotator import model

db = app.extensions['sqlalchemy'].db
es = app.extensions['pyes']

token = auth.generate_token('annotateit', 'admin')

ctx.pop()

# Push new test context with auth headers attached
ctx = app.test_request_context(headers=auth.headers_for_token(token).items())
ctx.push()

embed(display_banner=False)
