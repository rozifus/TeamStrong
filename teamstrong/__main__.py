import platform
platform.release = lambda:"10.6.5"
import interp
import data
import level

from schrocat import Schrocat

def main():
    """ your app starts here
    """
    # load the first level.
    #lev1 = open(data.filepath('levels/level1.json', 'data'))

    #repl = interp.IFRepl(level=level.load_level(lev1))
    #repl.cmdloop(": ")

    #ui.getapp().run()
    Schrocat().main_loop()
