import os

from annotator.app import app, setup_app

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(here, 'annotator.cfg')

    setup_app(config_file)
    app.run()

