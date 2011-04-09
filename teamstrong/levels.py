"""
Levels are just python objects with attributes.

"""
import random
import exceptions
import operator

getlevel = operator.itemgetter(2)

class LevelBase(object):
    """
    defines some base behaviours for a level.

    """

    @property
    def next_cat(self):
        return random.choice(self.catpositions)

    def get_vortexes_for_level(self, level):
        """
        Allow us to have vortexes that are progressively deployed during a
        level. 

        This returns all vortexes with a level value less than or equal to the
        one given.

        """
        return filter(lambda v: getlevel(v) < level, self.vortexes)

class LevelOne(LevelBase):
    """
    A pretty simple level, no obstacles just a cat and one vortex.

    cat can appear in multiple places (at random) after being hit.

    ^ = turret
    @ = vortex
    & = cat

    ----------------------
    |                    |
    |                    |
    |                    |
    |                  & |
    |         @  &   &   |
    |^                 & |
    ----------------------


    all locations are a faction of screen width and height. 

    """

    # tuple: ( (x, y), strength, level)
    vortexes = [
            ((0.5, 0.25), 0.3, 0),
    ]

    catpositions = [
                (0.6, 0.25),
                (0.8, 0.25),
                (0.9, 0.15),
                (0.9, 0.35),
    ]

    turret = (0, 0.15)
