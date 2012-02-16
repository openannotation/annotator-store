from IPython import embed

import annotator

app = annotator.create_app()
app.test_request_context().push()

from annotator import model

db = app.extensions['sqlalchemy'].db
es = app.extensions['pyes']

embed(display_banner=False)
