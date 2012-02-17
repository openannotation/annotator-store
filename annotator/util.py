from functools import update_wrapper

from flask import Response, request, json, flash, redirect, url_for, g

# We define our own jsonify rather than using flask.jsonify because we wish
# to jsonify arbitrary objects (e.g. index returns a list) rather than kwargs.
def jsonify(obj, *args, **kwargs):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return Response(res, mimetype='application/json', *args, **kwargs)

def require_user(func):
    """
    Decorator: ensure the global user object exists, otherwise redirect to the
    login page before executing the content of the view handler.
    """
    def requiring_user_first(*args, **kwargs):
        if not g.user:
            flash('Please log in')
            return redirect(url_for('user.login'))
        else:
            return func(*args, **kwargs)
    return update_wrapper(requiring_user_first, func)
