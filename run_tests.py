import os
import nose

if __name__ == '__main__':
    if not 'ANNOTATOR_CONFIG' in os.environ:
        here = os.path.abspath(os.path.dirname(__file__))
        os.environ['ANNOTATOR_CONFIG'] = os.path.join(here, 'tests', 'test.cfg')

    nose.run()


