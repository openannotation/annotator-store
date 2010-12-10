import os

import annotator.store as store
import annotator.model as model

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath( __file__ ))

    if 'ANNOTATOR_CONFIG' in os.environ:
        store.app.config.from_envvar('ANNOTATOR_CONFIG')
    else:
        store.app.config.from_pyfile(here + '/annotator.cfg')

    model.metadata.bind = store.app.config['DB']

    # Create tables
    model.setup_all(True)
    # Setup app
    store.setup_app()

    store.app.run()