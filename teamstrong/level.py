"""
Handles the parsing of level json files.

"""
from functools import partial
import json

import exceptions

def object_id(obj, objects):
    """
    returns the object id (key) for the given object.

    """
    for key, item in objects.items():
        if item['name'] == obj:
            return key

def children_of(obj, objects):
    """
    Return all of the children items of obj in objects.

    if obj is the root object, then all objects that are not inside
    another are returned.

    """
    ID, _ = obj
    isroot = root_object(objects) == obj

    children = {}
    for itemid, item in objects.items():

        location = item.get('location', None)
        position = item.get('position', None)

        object_inside = location == ID and position == "inside"
        root_child = isroot and position != "inside"

        if object_inside or root_child:
            children.update({itemid:item})

    return children

def root_object(objects):
    try:
        return filter(lambda (k,v): 'location' not in v, objects.items())[0]
    except IndexError:
        raise exceptions.NoRootObjectError(
                                    "This level has no root object,"
                                    " One object must not specify"
                                    " a location.")

def attr_list(objects, attr):
    """
    Returns a comma separated list of attr for
    the supplied objects

    """
    return  ', '.join('"%s"' % item[attr]
                    for item in objects.values())

name_list = partial(attr_list, attr="name")

def load_level(fileobj):
    return json.load(fileobj)
