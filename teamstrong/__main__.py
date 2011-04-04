import interp
import data
import level

def main():
    """ your app starts here
    """
    # load the first level.
    lev1 = open(data.filepath('levels/level1.json', 'data'))

    repl = interp.IFRepl(level=level.load_level(lev1))
    repl.cmdloop(": ")
