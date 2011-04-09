class NineTimesError(Exception):
    """Base exception for Nine Times game."""

class NoMoreVortexError(NineTimesError):
    """Cannot return any more vortexes, none exist."""
