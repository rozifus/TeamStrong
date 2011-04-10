'''Simple data loader module.

Loads data files from the "data" directory shipped with a game.

Enhancing this to handle caching etc. is left as an exercise for the reader.

Note that pyglet users should probably just add the data directory to the
pyglet.resource search path.
'''

import os
import sys

if 'python' in sys.executable:
    data_py = os.path.abspath(os.path.dirname(__file__))
else:
    data_py = os.path.abspath(os.path.dirname(sys.executable))



def _dir(dirname):
    return os.path.normpath(os.path.join(data_py, '..', dirname))

def filepath(filename, dirname="data"):
    '''Determine the path to a file in the data directory.
    '''
    return os.path.join(_dir(dirname), filename)

def load(filename, mode='rb', dirname="data"):
    '''Open a file in the data directory.

    "mode" is passed as the second arg to open().
    '''
    return open(os.path.join(_dir(dirname), filename), mode)

