__all__ = ("RollError", "RollSyntaxError", "RollValueError", "TooManyRolls")


class RollError(Exception):
    """Generic exception happened in the roll. Base exception for all library exceptions."""

    def __init__(self, msg):
        super().__init__(msg)


class RollSyntaxError(RollError):
    """Syntax error happened while parsing roll."""

    def __init__(self, line, col, got, expected):
        self.line = line
        self.col = col
        self.got = got
        self.expected = expected

        msg = f"Unexpected input on line {line}, col {col}: expected {', '.join([str(ex) for ex in expected])}, " \
              f"got {str(got)}"
        super().__init__(msg)


class RollValueError(RollError):
    """A bad value was passed to an operator."""
    pass


class TooManyRolls(RollError):
    """Too many dice rolled (in an individual dice or in rerolls)."""
    pass
