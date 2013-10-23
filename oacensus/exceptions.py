class OacensusError(Exception):
    pass

class UserFeedback(OacensusError):
    """
    An exception which was caused by user input or a runtime error and which
    should be presented nicely.
    """

class APIError(UserFeedback):
    """
    An exception raised by a remote API.
    """
    pass
