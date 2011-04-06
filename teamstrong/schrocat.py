#!/usr/bin/env python
from __future__ import print_function

import random
import math

import pyglet
from pyglet import window
from pyglet import clock
from pyglet import text

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

        self.cat = Cat(300, 300, self.batch,
                    self.images['catbody'], self.images['cathead'])
        self.actors.append(self.cat)

    def init_content(self):
        # load turret images, set rotational anchors, store for later
        frame = pyglet.image.load(data.filepath('frame.png'))
        frame.anchor_x = frame.width / 2
        frame.anchor_y = frame.height / 2
        self.images['frame'] = frame

        barrel = pyglet.image.load(data.filepath('barrel.png'))
        barrel.anchor_x = barrel.width / 2
        barrel.anchor_y = barrel.height / 4
        self.images['barrel'] = barrel

        cathead = pyglet.image.load(data.filepath('cathead.png'))
        cathead.anchor_x = cathead.width / 2
        cathead.anchor_y = cathead.height / 3
        self.images['cathead'] = cathead
        
        catbody = pyglet.image.load(data.filepath('catbody.png'))
        catbody.anchor_x = catbody.width / 2
        catbody.anchor_y = catbody.height / 2 
        self.images['catbody'] = catbody


    def main_loop(self):
		clock.set_fps_limit(30)

		while not self.has_exit:
			self.dispatch_events()
			self.update()
			self.clear()
			self.draw()

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
        pass


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
        print(self.head.rotation)

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
        print(self.barrel.rotation)

    def update(self):
        # just in case the turret ever needs to move
        self.frame.x, self.frame.y = self.x, self.y
        self.barrel.x, self.barrel.y = self.x, self.y

    def draw(self):
        # sprites are drawn directly by the batch
        pass

if __name__ == "__main__":
    schrocat = Schrocat()
    schrocat.main_loop()

