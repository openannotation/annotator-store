from IPython import embed

import annotator

annotator.create_app()
annotator.app.test_request_context().push()

embed(display_banner=False)
