import platform
platform.release = lambda:"10.6.5"
import data

from schrocat import Schrocat

from levels import LevelOne

def main():
    """ your app starts here
    """


    Schrocat(levels=[LevelOne]).main_loop()
