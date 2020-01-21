__all__ = ("RollError", "RollSyntaxError", "RollValueError", "TooManyRolls")


class RollError(Exception):
    """Generic exception happened in the roll."""

    def __init__(self, msg):
        super().__init__(msg)


class RollSyntaxError(RollError):
    """Syntax error happened while parsing roll."""

    def __init__(self, msg, line, col):
        super().__init__(msg)
        self.line = line
        self.col = col


class RollValueError(RollError):
    """A bad value was passed to an operator."""
    pass


class TooManyRolls(RollError):
    """Too many dice rolled (in an individual dice or in rerolls)."""
    pass
