class NineTimesError(Exception):
    """Base exception for Nine Times game."""

class NoRootObjectError(NineTimesError):
    """Level did not define a root object (i.e a room)."""
