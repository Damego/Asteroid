class AlreadyExistException(Exception):
    """
    Something already exists.
    """


class NotFound(Exception):
    """
    Something not found.
    """


class InvalidArgument(Exception):
    """
    Argument to a function is not valid
    """
