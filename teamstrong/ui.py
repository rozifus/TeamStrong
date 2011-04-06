import platform
platform.release = lambda:'10.6.0'
import pyglet

window = pyglet.window.Window()

label = pyglet.text.Label("The Nine Times",
                          font_name="Times New Roman",
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center')

class InteractiveElem(object):
    """
    Abstract base class that provides methods for interactivity.

    bind functions for:

    click, hover
    """

    def __init__(self, rect):
        """
        initalise with the rect that this object takes up.

        """
        self._rect = rect

    @property
    def rect(self):
        return self._rect

    def click(self, onclick=None, offclick=None, clickinfo=None):
        """
        set a callback for clicking and offclicking.

        """
        if onclick:
            self._onclick = onclick
        if offclick:
            self._offclick = offclick

        # exit if we were setting the callbacks.
        if onclick or offclick: return self

        # someone must have called without setting clickinfo.
        if not clickinfo: return self

        # a click has occurred did it hit us?
        coords = clickinfo.coords
        if not coords in self: return self

        # yes it is inside us. call back function.
        if clickinfo.buttondown:
            callback = self._onclick
        else: callback = self._offclick

        if callable(callback):
            callback(self)

        return self

    def __contains__(self, coords):
        return boundedby(coords, self.rect)

def boundedby(coords, rect):
    x, y, width, height
    insidex = x < coords.real < x + width
    insidey = y < coords.imag < y + height
    return insidex and insidey

# a simple console where user can enter text, and responses are
# sent back.

def draw_box(obj):
    x, y, width, height = obj.rect
    left = (x, y, x, y+height)
    right = (x+width,y,x+width,y+height)
    bottom = (x,y,x+width,y)
    top = (x,y+height,x+width,y+height)
    pyglet.graphics.draw(8, pyglet.gl.GL_LINES,
            ('v2i', left+right+bottom+top))

objects = [
        InteractiveElem([100, 50, 400, 60]),
                                
]

window.batch = pyglet.graphics.Batch()
document = pyglet.text.document.UnformattedDocument("hello: ")
layout = pyglet.text.layout.IncrementalTextLayout(
                document, 380, 60, multiline=False, batch=window.batch)
layout.x = 110
layout.y = 50

@window.event
def on_draw():
    window.clear()
    label.draw()
    for obj in objects:
        draw_box(obj)

def getapp():
    return pyglet.app
