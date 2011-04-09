#!/usr/bin/env python
from __future__ import print_function

import random
import math

import pyglet
from pyglet import window
from pyglet import clock
from pyglet import text
from pyglet import gl
import pymunk

# utilities for importing data files.
import data

from constants import G, FUDGE, DEFAULT_TYPE, BALL_TYPE, GRAVITY_TYPE, CAT_TYPE
from signals import register, signal
from utils import clip, get_or_setdefault, make_rotator, CrudeVec
from utils import distance, angle_between

#----------------------------------------------------------------
# Game in an object. Seriously the whole game is in Schrocat.

class Schrocat(window.Window):

    def __init__(self, *args, **kwargs):
        window.Window.__init__(self, *args, **kwargs)
        self.images = {}
        self.labels = {}
        self.actors = []
        self.batch = pyglet.graphics.Batch()
        self.interfaces = []

        # load our images
        self.init_content()

        # create a fps readout
        self.fps_label = text.Label('FPS goes here', 
                                    font_name='Arial', 
                                    font_size=10,
                                    x=10, y=10,)

        # create a turret
        self.turret = Turret(100, 100, self.batch,
                    self.images['frame'], self.images['barrel'])
        self.actors.append(self.turret)

        # schrocat live on.
        self.cat = Cat(300, 300, self.batch,
                    self.images['catbody'], self.images['cathead'])
        self.actors.append(self.cat)

        def make_callback_for(obj):

            def someonehit(*args, **kwargs):
                """ball or cat needs to remove 1 from meter qty."""
                obj.remove(qty=1)
            return someonehit

        self.ballMeter = Meter(10, 80, 50, 340,
                            (1.0,0.0,0.0), (0.0,1.0,0.0), 10, 5, True)
        self.catMeter = Meter(580, 80, 50, 340,
                            (1.0,0.0,0.0), (0.0,1.0,0.0), 10, 5, True)

        self.interfaces.append(self.ballMeter)
        self.interfaces.append(self.catMeter)

        # now make some callbacks to remove meter points when hit.
        callback = make_callback_for(self.ballMeter)
        register('shoot', callback)

        callback = make_callback_for(self.catMeter)
        register('cathit', callback)

        register('kill', self.remove_object)

    def remove_object(self, obj, *args, **kwargs):
        """
        try to remove this object and pretend it never existed.

        """
        try:
            self.actors.remove(obj)
        except ValueError:
            # puzzled. who did you want me to remove?
            pass 

    def init_content(self):
        # load turret images, set rotational anchors, store for later
        pymunk.init_pymunk()

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

        # This bit of code makes the balls pass through the gravity wells.
        # There are more efficient ways of doing this but I was experimenting
        # with collision handlers.
        def begin(space, arbiter):
            return False

        self.space.add_collision_handler(GRAVITY_TYPE, BALL_TYPE, 
                                            begin, None, None, None)

        def load_and_anchor(filename, anchor_x, anchor_y):
            """
            Returns a pyglet image whose x and y anchor points
            are set as a fraction of total width and height.
            """
            image = pyglet.image.load(data.filepath(filename))
            image.anchor_x = image.width // anchor_x
            image.anchor_y = image.height // anchor_y
            return image

        ball = load_and_anchor('ball.png', 2, 2)
        self.images['ball'] = ball

        frame = load_and_anchor('frame.png', 2, 2)
        self.images['frame'] = frame

        barrel = load_and_anchor('barrel.png', 2, 4)
        self.images['barrel'] = barrel

        cathead = load_and_anchor('cathead.png', 2, 3)
        self.images['cathead'] = cathead
        
        catbody = load_and_anchor('catbody.png', 2, 2)
        self.images['catbody'] = catbody

        gravity = load_and_anchor('gravity.png', 2, 2)
        self.images['gravity'] = gravity

    def main_loop(self):
        clock.set_fps_limit(30)

        while not self.has_exit:

            self.dispatch_events()
            self.update()
            self.clear()
            self.draw()

            # pymunk space update. updates position of all children.
            self.space.step(1/30.0)

            clock.tick()
            #Gets fps and draw it
            self.fps_label.text = "%d" % clock.get_fps()
            self.fps_label.draw()

            self.flip()

    def update(self):
        # update anything in the actorlist, turrets, cats, etc
        for actor in self.actors:
            actor.update()

        for interface in self.interfaces:
            interface.update()

    def draw(self):
        self.batch.draw()

        for i in self.interfaces:
            i.draw()

    """ Event Handlers """

    def on_mouse_motion(self, x, y, dx, dy):
        # tell the turret where the cursor is pointed
        self.turret.aim(x,y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        """
        Create a new bullet at the turret. (LEFT CLICK)
        Create a new gravity well. (RIGHT CLICK).
        """

        # left click make a bullet.
        if button == 1:

            if self.ballMeter.active:
                # signal that we are making a bullet.
                signal('shoot')
                self._bullet(x, y)
            
        elif button == 4:
            self._gravity(x, y)
            self.ballMeter.add(3)
        
    @property
    def gravities(self):
        """Return a list of all gravities."""
        return filter(lambda s: s.__class__.__name__ == 'Gravity', self.actors)

    def _gravity(self, x, y):
        """Make a gravity well near the click location."""
        gravity = make_gravity(x, y, self.batch, self.images['gravity'],
                                self.space)
        gravity.parent = self
        self.actors.append(gravity)

    def _bullet(self, x, y):
        """Make a bullet and add it near the turret."""
        xTip, yTip = self.turret.tip
        angle = self.turret.rotation
        
        minLaunchVel = 10
        maxLaunchVel = 600
        refDist = 250.0

        # Velocity is dependent on the distance the pointer is from the turret.
        # As this is a ratio, I removed the sqrt and squared the distance it
        # will is divided by.

        _ = CrudeVec
        speed = maxLaunchVel * distance(_(x, y), _(xTip, yTip)) / refDist
        speed = clip(maxLaunchVel, minLaunchVel)(speed)

        # create a crude velocity.
        velx = math.sin(angle) * speed
        vely = math.cos(angle) * speed

        ball = make_ball(xTip, yTip, self.batch, self.images['ball'],
                        self.space)
        ball.velocity = (velx, vely)
        ball.parent = self

        self.actors.append(ball)

#---------------------------------------------------------------------
# Game objects.

class PhysicsElem(object):
    """An object that is Physics aware."""

    def __init__(self, mass, radius, x, y, batch, image, space):

        self.mass = mass
        self.image = pyglet.sprite.Sprite(image, batch=batch)

        inertia = pymunk.moment_for_circle(mass, 0, radius)
        self.body = body = pymunk.Body(mass, inertia)
        body.position = x, y
        self.shape = shape = pymunk.Circle(body, radius)
        space.add(body, shape)

    @property
    def x(self):
        return self.body.position.x

    @property
    def y(self):
        return self.body.position.y

    @property
    def velocity(self):
        return self.body.velocity

    @velocity.setter
    def velocity(self, value):
        self.body.velocity = value

    @property
    def force(self):
        return self.body.force

    @force.setter
    def force(self, value):
        self.body._set_force(value)

    def hit(self, other):
        """Returns True if this x, y pair is inside the other."""
        return (self.x, self.y) in other

    @property
    def collision_type(self):
        return self.shape._get_collision_type

    @collision_type.setter
    def collision_type(self, value):
        self.shape._set_collision_type(value)

    def update(self):
        """convert body.position co-ords to self.image.x and y coords."""
        self.image.x = self.x
        self.image.y = self.y
        self.custom_update()

    def custom_update(self):
        """
        Override this to add custom functionality in update.
        """
        pass

    def __contains__(self, x_y):
        return self.body.point_query(x_y)


class Ball(PhysicsElem):
    """A ball shot from a cannon."""

    def __init__(self, mass, radius, x, y, batch, image, space):
        PhysicsElem.__init__(self, mass, radius, x, y, batch, image, space)
        self.collision_type = BALL_TYPE

    def custom_update(self):
        """
        Find the net force from all of the gravities to me!

        Then work out if I have hit a cat or something...
        """
        gravities = self.parent.gravities

        forcex,forcey = 0,0
        for gravity in gravities:
            _forcex, _forcey = gravity.force_on(self)
            forcex += _forcex
            forcey += _forcey

        self.force = (forcex, forcey)

        # have I hit a cat?
        if self.hit(self.parent.cat):
            signal('cathit')
            # well I did. I should surely die now.
            signal('kill', self)
            
class Gravity(PhysicsElem):
    """A gravitational well."""

    def __init__(self, mass, radius, x, y, batch, image, space):
        PhysicsElem.__init__(self, mass, radius, x, y, batch, image, space)
        self.collision_type = GRAVITY_TYPE

    def custom_update(self):
        """
        Update rotation so that it is always spinning.

        """
        # gravity will spin in a random direction for visual gags.
        direction = get_or_setdefault(self, '_direction',
                                            random.choice([3, -3]))

        rotator = get_or_setdefault(self, '_rotator',
                                            make_rotator(direction))

        self.image.rotation = rotator.next()

    def force_on(self, obj):
        """
        Returns the force on an object that defines x and y properties.

        """
        force = G * FUDGE * self.mass * obj.mass / distance(self, obj) ** 2
        # angle from ball to this gravity.
        angle = angle_between(obj, self)

        return force * math.cos(angle), force * math.sin(angle)

class Cat(object):
    def __init__(self, x, y, batch, body, head):
        self.x, self.y = x,y

        self.body = pyglet.sprite.Sprite(body, batch=batch)
        self.head = pyglet.sprite.Sprite(head, batch=batch)

        self.getHeadTilt = make_rotator(lim_left=-10, lim_right=10)

    def update(self):
        """
        Updates the head.. 
        """
        self.body.x, self.body.y = self.x , self.y
        self.head.x, self.head.y = self.x - 6 , self.y + 10 
        self.head.rotation = self.getHeadTilt.next()

    def hit(self, other):
        """Returns True if this x, y pair is inside the other."""
        return (self.x, self.y) in other

    def __contains__(self, x_y):
        x, y = x_y
        within_x = self.body.x < x and x < self.body.x + self.body.width
        within_y = self.body.y < y and y < self.body.y + self.body.height

        return within_x and within_y

class Turret(object):
    length = 60

    def __init__(self, x, y, batch, frame, barrel):
        self.x, self.y = x,y

        # create sprites for the turret from images
        self.frame = pyglet.sprite.Sprite(frame, batch=batch) 
        self.barrel = pyglet.sprite.Sprite(barrel, batch=batch) 

    def aim(self, x, y):
        # this could possible be simpler, i don't like trig much :( 
        self.barrel.rotation = (math.degrees(math.atan2(self.x-x, self.y-y)) + 180) % 360
        if self.barrel.rotation > 90 and self.barrel.rotation < 270:
            if self.barrel.rotation < 180:
                self.barrel.rotation = 90
            else: self.barrel.rotation = 270

    @property
    def tip(self):
        """
        Return the x, y co-ordinates of the tip of the barrel.
        Uses an estimated length of the barrel based on size of the image.

        """
        # in degrees clockwise from vertical.
        rot = self.rotation

        # x + delta_x = x + sin(theta) * L
        x = self.x + math.sin(rot) * self.length
        y = self.y + math.cos(rot) * self.length
        return x, y

    @property
    def rotation(self):
        """return rotation in radians."""
        return math.radians(self.barrel.rotation)

    def update(self):
        # just in case the turret ever needs to move
        self.frame.x, self.frame.y = self.x, self.y
        self.barrel.x, self.barrel.y = self.x, self.y

    def draw(self):
        # sprites are drawn directly by the batch
        pass

#----------------------------------------------------------
# Object factory functions.

def make_ball(x, y, batch, image, space, mass=1, radius=5):
    return Ball(mass, radius, x, y, batch, image, space)

def make_gravity(x, y, batch, image, space, mass=1e6, radius=50):
    return Gravity(mass, radius, x, y, batch, image, space)

#-----------------------------------------------------------
# Interface objects.

class Meter(object):

    def __init__(self, x, y, width, height,
                 minColor, maxColor, maxPoints,
                 initPoints=None, gradient=False, visible=True):

        self.x, self.y = x,y
        self.width, self.height = width, height
        self.maxPoints = maxPoints
        self.minColor, self.maxColor = minColor, maxColor
        self.points = initPoints or maxPoints
        self.visible = visible

        # a fraction of 1, despite pc (percent)
        self.pointpc = 0.0 
        self.color = (1.0, 1.0, 1.0)

        self.gradient = gradient
        self.update()

    @property
    def top(self):
        return self.y + self.height*self.pointpc

    @property
    def bottom(self):
        return self.y

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def active(self):
        """So long as this baby has 'points' it is active."""
        return self.points

    def update(self):
        # get points as percentage of maximum
        self.pointpc = float(self.points) / self.maxPoints

        # produce intermediate color
        pointpc, inverse = self.pointpc, 1 - self.pointpc
        self.color = (
                self.minColor[0] * inverse +
                self.maxColor[0] * pointpc,

                self.minColor[1] * inverse +
                self.maxColor[1] * pointpc,

                self.minColor[2] * inverse +
                self.maxColor[2] * pointpc)

        # not sure if necessary, but in case of rounding errors            
        self.color = map(clip(1, 0), self.color)

    def draw(self):
        """
        Black magic.

        """
        # draw the rect
        if not self.visible:
            # lol, don't do anything if not visible.
            return

        gl.glLoadIdentity()
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(*self.color)
        gl.glVertex2f(self.left, self.top)
        gl.glVertex2f(self.right, self.top)

        if self.gradient:
            gl.glColor3f(*self.minColor)

        gl.glVertex2f(self.right, self.bottom)
        gl.glVertex2f(self.left, self.bottom)
        gl.glEnd()

    def add(self, qty=1):
        """
        Add qty to points, but clip at maxPoints.

        """
        self.points = min(self.points + qty, self.maxPoints)

    def remove(self, qty=1):
        """
        Return the number of points after removing qty points.

        Python treats any number of points other than 0 to be True.
        """
        self.points = max(self.points - qty, 0)
        return self.points


