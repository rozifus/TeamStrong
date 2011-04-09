import itertools
import math

#-----------------------------------------------------------
# Utility functions.

def make_play_sound_callback(sound_function):
    """
    Returns a wrapper around the pyglet.resources.sounds.play function that
    accepts *args, and **kwargs required of all callbacks.

    """
    def callback(*args, **kwargs):
        sound_function()
    return callback

def get_or_setdefault(obj, attr, default):
    """
    Get an attribute from an object, if it doesn't exist set the default
    attribute on the object.

    """
    value = getattr(obj, attr, default)
    setattr(obj, attr, value)
    return value

def make_rotator(step=1, lim_left=None, lim_right=None):
    """
    returns a generator function that will rotate
        until it hits left then back until it hits right.
    args:
        step: number of degrees to rotate per iteration.
        lim_left: the counter_clockwise bound angle limit.
        lim_right: the clockwise bound angle limit.
    """
    # two rotators could be made, one with limits one without.
    if lim_left is not None and lim_right is not None:
        def rotator():
            rotation = 0
            direction = 1 * step
            while 1:
                if lim_left > rotation or lim_right < rotation:
                    direction = direction * -1

                rotation += direction
                yield rotation

        return rotator()

    # a simple rotator that only goes in one direction.
    def rotator():
        counter = itertools.count()
        while 1:
            yield (counter.next() * step % 360)
    return rotator()

class CrudeVec(complex):
    """
    a crude (but clever?) Vector.
    """

    @property
    def x(self):
        return self.real

    @property
    def y(self):
        return self.imag

def distance(left, right):
    """
    Return the distance between the left and right objects.

    """
    return math.hypot(left.x - right.x, left.y - right.y)

def angle_between(center, other):
    """
    Find the radian angle from the center object to the other object.

    """
    x = other.x - center.x
    y = other.y - center.y

    return math.atan2(y, x)

def clip(upper, lower):
    """
    return a function that clips its argument to upper and lower bounds.
    
    """
    def _(value):
        """Oh so sneaky."""
        return max(min(upper, value), lower)

    return _

