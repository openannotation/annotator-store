import os
import sys
import inspect

import annotator.model as model
import annotator.store as store

class Command:
    def __init__(self, model):
        self.model = model

    def create(self):
        """
        Create a new consumer, returning the consumer key and secret.
        """
        import os
        import hashlib

        key    = hashlib.sha1(os.urandom(64)).hexdigest()
        secret = hashlib.sha256(os.urandom(512)).hexdigest()

        c = self.model.Consumer(key=key, secret=secret)
        self.model.session.commit()

        import json
        print json.dumps(c.to_dict(), indent=2)

    def get(self, key):
        """
        Get and print the details of the consumer key specified
        """

        c = self.model.Consumer.get(key)

        if c:
            import json
            print json.dumps(c.to_dict(), indent=2)
        else:
            sys.exit(1)

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath( __file__ ))

    if 'ANNOTATOR_CONFIG' in os.environ:
        store.app.config.from_envvar('ANNOTATOR_CONFIG')
    else:
        store.app.config.from_pyfile(here + '/annotator.cfg')

    model.metadata.bind = store.app.config['DB']

    # Create tables
    model.setup_all(True)

    if len(sys.argv) >= 2:
        command = sys.argv[1]
        runner = Command(model)

        if hasattr(runner, command):
            getattr(runner, command)(*sys.argv[2:])
        else:
            print "Command not known: %s" % command
    else:
        print "Usage: python %s <command> [args...]" % (__file__)
        print
        print "Commands:"
        for name, member in inspect.getmembers(Command):
            doc = inspect.getdoc(member)
            if inspect.ismethod(member) and doc:
                print "    %s %s" % (name.ljust(10), inspect.getdoc(member))
