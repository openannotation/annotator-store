import os
import sys
import optparse
import inspect

from annotator.app import setup_app as _setup_app
import annotator.model as model


def fixtures():
    '''Create some fixtures (e.g. for demoing).'''
    acc = model.User.get('tester')
    if acc is None:
        acc = model.User(
            id='tester',
            username='tester',
            email='tester@annotateit.org'
            )
        acc.password = 'pass'
        acc.save()
    for x in [1,2,3]:
        anno = model.Annotation(
            consumer_key='annotateit',
            user=user.id,
            text=x*str(x)
            )
        anno.save()
    print 'Fixtures created (tester@annotateit.org / pass)'


def _module_functions(functions):
    local_functions = dict(functions)
    for k,v in local_functions.items():
        if not inspect.isfunction(v) or k.startswith('_'):
            del local_functions[k]
    return local_functions

def _main(functions_or_object):
    isobject = inspect.isclass(functions_or_object)
    if isobject:
        _methods = _object_methods(functions_or_object)
    else:
        _methods = _module_functions(functions_or_object)

    usage = '''%prog {action}

Actions:
    '''
    usage += '\n    '.join(
        [ '%s: %s' % (name, m.__doc__.split('\n')[0] if m.__doc__ else '') for (name,m)
        in sorted(_methods.items()) ])
    parser = optparse.OptionParser(usage)
    # Optional: for a config file
    # parser.add_option('-c', '--config', dest='config',
    #         help='Config file to use.')
    options, args = parser.parse_args()

    if not args or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    if isobject:
        getattr(functions_or_object(), method)(*args[1:])
    else:
        _methods[method](*args[1:])

__all__ = [ '_main' ]

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(here, 'annotator.cfg')

    _setup_app(config_file)
    _main(locals())

