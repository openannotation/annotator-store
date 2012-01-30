import os

if not 'ANNOTATOR_CONFIG' in os.environ:
    here = os.path.dirname(__file__)
    os.environ['ANNOTATOR_CONFIG'] = os.path.join(here, 'test.cfg')

import nose.tools as helpers
