import os

from annotator.annotator import app, setup_app
from annotator.model import *

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath( __file__ ))

    if 'ANNOTATOR_CONFIG' in os.environ:
        app.config.from_envvar('ANNOTATOR_CONFIG')
    else:
        app.config.from_pyfile(here + '/annotator.cfg')

    metadata.bind = app.config['DB']

    # Create tables
    setup_all(True)
    # Setup app
    setup_app()

    app.run()