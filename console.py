from IPython import embed

import annotator

annotator.create_app()
annotator.app.test_request_context().push()

from annotator import app, db, es, model

embed(display_banner=False)
