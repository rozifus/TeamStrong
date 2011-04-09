"""
Signal registry
===============

handles callbacks between distant objects.

list of signals for easy reference:

'shoot': a ball is shot.
'cathit': a cat got hit by a ball.
'catdead': a cat is dead.

example of use:

    register('shoot', do_something_when_ball_shoots)

    # (..) later in the code..

    signal('shoot', argument, keyword=keywordargstoo)

    # at this point 'do_something_when_ball_shoots' gets called with 
    # all arguments and keyword arguments.
"""
import collections

_register = collections.defaultdict(list)

def register(name, callback):
    """Register a callback function for a signal called 'name'"""

    if callback in _register[name]:
        # bugger off, you have registered once for this signal before.
        return

    _register[name].append(callback)

def signal(name, *args, **kwargs):
    """Signal to all callback functions listening to 'name'."""

    for fn in _register[name]:
        fn(*args, **kwargs)

