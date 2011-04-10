#!/usr/bin/env python
from __future__ import print_function

import random
import math
import time

import pyglet
from pyglet.media import Player, StaticSource, StreamingSource
from pyglet.media import load as load_media
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
from utils import distance, angle_between, make_play_sound_callback

#----------------------------------------------------------------
# Game in an object. Seriously the whole game is in Schrocat.

class Schrocat(window.Window):

    def __init__(self, *args, **kwargs):
        """Expects a levels keyword argument."""
        self.levels = levels = kwargs.pop('levels')
        self.level = level = levels[0]()

        super(Schrocat, self).__init__(*args, **kwargs)

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
        # window width and height.
        width, height = self.get_size()

        # create a turret
        (turx, tury) = level.turret
        self.turret = Turret(turx * width, tury * height, self.batch,
                    self.images['frame'], self.images['barrel'])
        self.turret.initPowerBar(self.images['powerbar'], self.batch, 4, 25, 70)
                
        self.actors.append(self.turret)

        #----------------------
        # schrocat live on.
        catx, caty = level.next_cat
        cat = self._cat(catx * width, caty * width)

        #----------------------
        # make a bunch of vortexes..
        vortexes_or_vortecii_which_is_correct = level.get_vortexes_for_level(1)
        for v in vortexes_or_vortecii_which_is_correct:
            (x, y), strength, level = v
            gravity = self._gravity(x * width, y * height)
            gravity.strength = strength

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

        x = load_and_anchor('x.png', 2, 2)
        self.images['x'] = x

        trail = load_and_anchor('trail.png', 2, 2)
        self.images['trail'] = trail

        powerbar = load_and_anchor('powerbar.png', 2, 2)
        self.images['powerbar'] = powerbar

        #-------------------------------
        # load up some sounds.
        self.sounds = {}

        self.sounds['gravity'] = load_sound('gravityhit.wav')
        self.sounds['cathit'] = load_sound('cathit.wav')

        register('vortexhit', make_play_sound_callback(
                                    self.sounds['gravity'].play))

        register('cathit', make_play_sound_callback(
                                    self.sounds['gravity'].play))
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

                # make a new X marks the spot.
                x = self._xmark(x, y)
            
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
        register('vortexhit', gravity.hitbyball)
        return gravity

    def _bullet(self, x, y):
        """Make a bullet and add it near the turret."""
        xTip, yTip = self.turret.tip
        angle = self.turret.rotation
        
        maxLaunchVel = 600
        
        speed = self.turret.power * maxLaunchVel

        # create a crude velocity.
        velx = math.sin(angle) * speed
        vely = math.cos(angle) * speed

        ball = make_ball(xTip, yTip, self.batch, self.images['ball'],
                        self.space)
        ball.velocity = (velx, vely)
        ball.parent = self

        self.actors.append(ball)
        return ball

    def _cat(self, x, y):
        self.cat = Cat(x, y, self.batch,
                    self.images['catbody'], self.images['cathead'])
        self.cat.parent = self
        self.actors.append(self.cat)
        register('cathit', self.cat.move)
        return self.cat

    def _xmark(self, x, y):
        x = make_x(x, y, self.batch, self.images['x'])
        self.actors.append(x)
        return x

    def onscreen(self, x, y):
        """
        Returns true if the given x, y is on screen.

        """
        within_x = 0 < x and x < self.width
        within_y = 0 < y and y < self.height

        return within_x and within_y

#---------------------------------------------------------------------
# Game objects.

class PhysicsElem(object):
    """An object that is Physics aware."""

    def __init__(self, mass, radius, x, y, batch, image, space):

        self.mass = mass
        self.radius = radius

        self.image = pyglet.sprite.Sprite(image, batch=batch)

        inertia = pymunk.moment_for_circle(mass, 0, radius)
        self.body = body = pymunk.Body(mass, inertia)
        body.position = x, y
        self.shape = shape = pymunk.Circle(body, radius)
        space.add(body, shape)

    def grow(self, fraction):
        """
        grow the size of the image and the pymunk shape by a fraction.

        """
        self.image.scale += fraction
        radius, mass = self.radius, self.mass
        x, y = self.x, self.y

        self.parent.space.remove(self.shape)
        radius = radius * math.sqrt(fraction)
        
        inertia = pymunk.moment_for_circle(mass, 0, radius)
        self.body = body = pymunk.Body(mass, inertia)
        body.position = x, y
        self.shape = shape = pymunk.Circle(body, radius)
        self.parent.space.add(body, shape)

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
        return self.shape.point_query(x_y)


class Ball(PhysicsElem):
    """A ball shot from a cannon."""

    def __init__(self, mass, radius, x, y, batch, image, space):
        PhysicsElem.__init__(self, mass, radius, x, y, batch, image, space)
        self.collision_type = BALL_TYPE

    def custom_update(self):
        """
        Find the net force from all of the gravities to me!

        Then work out if I have hit a cat or something...

        also lay a trail as we go.
        """
        gravities = self.parent.gravities

        forcex,forcey = 0,0
        for gravity in gravities:
            _forcex, _forcey = gravity.force_on(self)
            forcex += _forcex
            forcey += _forcey

            # have I hit a vortex?
            if self.hit(gravity):
                signal('vortexhit', gravity=gravity, ball=self)

                # well if that is the case, then time for me to die.
                signal('kill', self)

        self.force = (forcex, forcey)

        # have I hit a cat?
        if self.hit(self.parent.cat):
            signal('cathit')
            # well I did. I should surely die now.
            signal('kill', self)

        # leave a trail but only if we are on the screen.
        if not self.parent.onscreen(self.x, self.y):
            return

        trail = X(self.x, self.y, self.parent.batch, self.parent.images['trail'])
        trail.minopacity = 1
        trail.rate = 1.01
        self.parent.actors.append(trail)
            
class Gravity(PhysicsElem):
    """A gravitational well."""

    def __init__(self, mass, radius, x, y, batch, image, space):
        PhysicsElem.__init__(self, mass, radius, x, y, batch, image, space)
        self.collision_type = GRAVITY_TYPE
        self._strength = 0.1

    def hitbyball(self, gravity, ball):
        """
        A callback method that takes the gravity that was hit, and
        the ball that hit it.

        """
        # check, was I the gravity that was hit?
        if not gravity is self:
            return

        # I have been hit by a ball, need to upgrade my strength.
        # and mabbe get a bit bigger.
        self.strength = self.strength + 0.2
        self.grow(0.2)

    @property
    def strength(self):
        return self._strength

    @strength.setter
    def strength(self, value):
        self._strength = value

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

        # adjust for this gravity strength.
        force = self.strength * force

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

    def move(self):
        """I got hit, the jig is up. time to move on."""
        x, y = self.parent.level.next_cat
        width, height = self.parent.get_size()
        self.x, self.y = x * width, y * height

    def __contains__(self, x_y):
        x, y = x_y
        within_x = self.body.x < x and x < self.body.x + self.body.width
        within_y = self.body.y < y and y < self.body.y + self.body.height

        return within_x and within_y

class X(object):
    def __init__(self, x, y, batch, image, opacity=255):
        self.image = pyglet.sprite.Sprite(image, batch=batch)
        self.image.opacity = opacity
        self.x, self.y = x, y
        self.opacity = opacity
        self.minopacity = 1
        self.rate = 1.005
        self.seconds_to_live = 10
        self.created_at = time.time()

    def update(self):
        self.opacity = self.opacity / self.rate
        self.image.opacity = int(self.opacity)
        self.image.position = (self.x, self.y)

        if self.opacity < self.minopacity:
            signal('kill', self)
        elif time.time() - self.created_at > self.seconds_to_live:
            signal('kill', self)


class PowerBar(object):
    def __init__(self, image, batch, nBars, smallWid, bigWid):
        self.nBars = nBars
        self.sprites = []
        for i in range(nBars):
            self.sprites.append(pyglet.sprite.Sprite(image, batch=batch))
        
        # scaling required to get the first bar to be 'bigWid'
        bigScale = float(bigWid) / self.sprites[0].width
        smallScale = float(smallWid) / self.sprites[0].width
        
        smallCol = (0,0,255) #blue
        bigCol = (255,0,0) #red
        
        def colMix(col1, col2, ratio):
            """
            Linear interpolation between col1 and col2
            """
            r = int(ratio * (col1[0] - col2[0])) + col2[0]
            g = int(ratio * (col1[1] - col2[1])) + col2[1]
            b = int(ratio * (col1[2] - col2[2])) + col2[2]
            return (r, g, b)
        
        colorStep = 1.0 /(nBars -1)
        currColor = 1.0
        scaleStep = (bigScale - smallScale) / (nBars-1)
        currScale = smallScale
        self.barOffsets = []
        currHeight = 0
        # start from small to large bar
        for sprite in self.sprites:
            sprite.scale = currScale
            # set scale for the next step.
            currScale += scaleStep

            self.barOffsets.append(currHeight)
            # set height for next bar.
            currHeight += sprite.height

            sprite.color = colMix(smallCol, bigCol, currColor)
            # set colour ratio for the next bar.
            currColor -= colorStep

            sprite.visible = False
            

        
    def updatePos(self, x, y, rot):
        """
        Move all of the bars so the stay in formation

        """
        for i, sprite in enumerate(self.sprites):
            sprite.x = x + math.sin(math.radians(rot)) * self.barOffsets[i]
            sprite.y = y + math.cos(math.radians(rot)) * self.barOffsets[i]
            sprite.rotation = rot

    def updatePower(self, power):
        """
        This draws the different bars of the powerBar with varying opacity.

        For instance, if there are four bars, then the power rating will be
        split into 4 sections, 0-25, 25-50 etc. Only the first bar will be 
        visible if the power is in the first band. Its opacity (out of a
        max set by maxOpac) will be relative to its magnitude in this range; 
        section 2 will barely be visible if the power is 28% but almost
        completly opaque when approaching 50%.

        """
        maxOpac = 200
        bandSize = 1.0 / self.nBars
        for i, sprite in enumerate(self.sprites):
            # divide the power bars into sections. ie. if there are 4 bars
            # and power is only .20 then only the first bar is visible and
            # only (.20/.25) of the max oppacity
            if power < float(i) / self.nBars:
                # underpowered :(
                sprite.visible = False
            elif power < (float(i) + 1) /self.nBars:
                # power in this section
                sprite.visible = True
                # opac = maxOpac * ( amount past threshold / size of band)
                sprite.opacity = int(maxOpac * 
                                    (power - (float(i)) /self.nBars) /
                                    bandSize)
            else:
                # Over powered!!!
                sprite.visible = True
                sprite.opacity = maxOpac

        

class Turret(object):
    length = 60

    def __init__(self, x, y, batch, frame, barrel):
        self.x, self.y = x,y

        # create sprites for the turret from images
        self.frame = pyglet.sprite.Sprite(frame, batch=batch) 
        self.barrel = pyglet.sprite.Sprite(barrel, batch=batch) 

        
    def initPowerBar(self, image, batch, nBars, smallWid, bigWid):
        self.powerBar = PowerBar(image, batch, nBars, smallWid, bigWid)

    def aim(self, x, y):
        # this could possible be simpler, i don't like trig much :( 
        self.barrel.rotation = (math.degrees(math.atan2(self.x-x, self.y-y)) + 180) % 360
        
        if self.barrel.rotation > 90 and self.barrel.rotation < 270:
            if self.barrel.rotation < 180:
                self.barrel.rotation = 90
            else: self.barrel.rotation = 270

        # update power and other things to do with the aim.    
        self.updatePower(x, y)
        self.powerBar.updatePower(self.power)
        xTip, yTip = self.tip
        self.powerBar.updatePos(xTip, yTip, self.barrel.rotation)

    def updatePower(self, x, y):
        """
        Compute the power!!!

        Measured as the distance from the tip of the turret.
        """
        refDist = 250.0
        xTip, yTip = self.tip
        # Velocity is dependent on the distance the pointer is from the turret.
        _ = CrudeVec
        self.power = distance(_(x, y), _(xTip, yTip)) / refDist
        self.power = clip(1.0, 0.05)(self.power)


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

def make_x(x, y, batch, image):
    return X(x, y, batch, image)

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

def load_sound(filepath, streaming=False):
    """
    Load a sound using pyglet resource. set streaming to true if this
    is a background music sound.

    """
    SoundClass = StaticSource
    if streaming:
        SoundClass = StreamingSource

    # for now return a fake class because I am getting AVBin exceptions
    # where i cannot load the .wav files?
    class Fake(object):
        def play(self):
            pass

    return Fake()

    return SoundClass(load_media(data.filepath(filepath), streaming=streaming))
