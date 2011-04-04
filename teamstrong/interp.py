"""
File to house the main interactive fiction console.

Loads up and runs stored json levels.
"""

import cmd

from level import children_of, root_object, name_list

class IFRepl(cmd.Cmd):
    """
    An interactive fiction REPL. Simple commands to interact with a
    level.
    """
    def __init__(self, *args, **kwargs):

        self.level = kwargs.pop('level')

        # not a new style class, cannot use super.
        cmd.Cmd.__init__(self, *args, **kwargs)

    def output(self, msg):
        self.stdout.write(msg)

    def do_quit(self, arg):
        """
        Exit the game.

        """
        import sys
        sys.exit(0)

    def postcmd(self, stop, line):
        self.output("%s\n" % stop)

    def do_list(self, arg):
        """
        lists all objects in this scene.

        When called with an object, lists all objects inside that
        object.

        e.g. "list desk" will list all objects inside the desk.

        """

        objects = self.level['objects']
        requested_object = arg.strip().lower()

        items = None
        if not requested_object:
            # the user didn't say "list desk" so list everything.
            items = name_list(
                    children_of(
                        root_object(objects), objects))

        # must have said "list desk" so list children of "desk" obj.
        for key, obj in objects.items():
            if obj['name'].lower() == requested_object:
                items = name_list(
                        children_of((key, obj), objects))

        if items:
            return items

        return "sorry %s doesn't contain anything" % requested_object
