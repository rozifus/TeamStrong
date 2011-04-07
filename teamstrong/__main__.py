import platform
platform.release = lambda:"10.6.5"
import data

from schrocat import Schrocat

def main():
    """ your app starts here
    """


    Schrocat().main_loop()
