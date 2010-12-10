import os

from annotator import app
from annotator.model import *

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath( __file__ ))

    metadata.bind = "sqlite:///%s/db/annotator.sqlite" % here

    setup_all(True)

    app.run()