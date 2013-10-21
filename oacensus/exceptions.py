class OacensusError(Exception):
    pass

class APIError(OacensusError):
    """
    An exception raised by a remote API.
    """
    pass
