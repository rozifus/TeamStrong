#!/usr/bin/env python
from __future__ import print_function

import random
import math

import pyglet
from pyglet import window
from pyglet import clock
from pyglet import text
import pymunk

# utilities for importing data files.
import data

class Schrocat(window.Window):

    def __init__(self, *args, **kwargs):
        window.Window.__init__(self, *args, **kwargs)
        self.images = {}
        self.labels = {}
        self.actors = []
        self.batch = pyglet.graphics.Batch()

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

    def init_content(self):
        # load turret images, set rotational anchors, store for later
        pymunk.init_pymunk()

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

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

    def draw(self):
        self.batch.draw()

    """ Event Handlers """

    def on_mouse_motion(self, x, y, dx, dy):
        # tell the turret where the cursor is pointed
        self.turret.aim(x,y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        """Create a new bullet at the turret."""

        x, y = self.turret.tip
        angle = self.turret.rotation

        speed = 100
        # create a crude velocity.
        velx = math.sin(angle) * speed
        vely = math.cos(angle) * speed

        ball = make_ball(x, y, self.batch, self.images['ball'],
                        self.space)
        ball.velocity = (velx, vely)

        self.actors.append(ball)


def make_ball(x, y, batch, image, space, mass=1, radius=5):
    return Ball(mass, radius, x, y, batch, image, space)

class Ball(object):
    """A ball shot from the cannon."""

    def __init__(self, mass, radius, x, y, batch, image, space):

        self.image = pyglet.sprite.Sprite(image, batch=batch)

        inertia = pymunk.moment_for_circle(mass, 0, radius)
        self.body = body = pymunk.Body(mass, inertia)
        body.position = x, y
        shape = pymunk.Circle(body, radius)
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

    def update(self):
        """convert body.position co-ords to self.image.x and y coords."""
        self.image.x = self.x
        self.image.y = self.y


class Cat(object):
    def __init__(self, x, y, batch, body, head):
        self.x, self.y = x,y

        self.body = pyglet.sprite.Sprite(body, batch=batch)
        self.head = pyglet.sprite.Sprite(head, batch=batch)

        self.getHeadTilt = self.headTiltGen()

    def update(self):
        self.body.x, self.body.y = self.x , self.y
        self.head.x, self.head.y = self.x - 6 , self.y + 10 
        self.head.rotation = self.getHeadTilt.next()

    def headTiltGen(self):
        # a generator for cat's head tilt
        leftToRight = True
        rotation = 0.00
        while 1:
            if rotation > 10:
                leftToRight = False
            elif rotation < -10:
                leftToRight = True
            if leftToRight:
                rotation += 1 
            else: rotation -= 1 
            yield rotation 


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

