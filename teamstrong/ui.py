"""
A splash screen for our game.
User can choose to read some information about the game, select a level
or exit.

"""

import pyglet

import simplui as ui
import levels
import schrocat

import data
import utils

window = schrocat.Schrocat(640, 480, caption='schrodengers cat',
        vsync=False)

themes = [ui.Theme(data.filepath('themes/pywidget'))]
theme = 0

frame = ui.Frame(themes[theme], w=640, h=480)

img = pyglet.sprite.Sprite(schrocat.load_and_anchor('SplashScreen.png'))

def onlevel(lvl):
    """
    Start Schrocat window with this level as an argument

    """
    def _(*args):
        window.init(levels=[lvl]).main_loop()
    return _

lvls = [levels.LevelOne, levels.LevelTwo, levels.LevelThree]

lvl_buttons = [
        ui.Button('Level %d' % (i + 1), action=onlevel(lvl))
        for (i, lvl) in enumerate(lvls)
]
window.push_handlers(frame)

dialogue = ui.Dialogue('Schrodingers Cat', x=520, y=380, content=
        ui.VLayout(w=200, hpadding=20,
                   children=lvl_buttons
        )
)

frame.add(dialogue)

@window.event
def on_draw():

    if window._window_active:
        return

    window.clear()
    img.draw()
    frame.draw()

def update(dt): pass

pyglet.clock.schedule(update)

pyglet.app.run()
