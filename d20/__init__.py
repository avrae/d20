from .dice import *
from . import diceast as ast
from .errors import *
from .models import *
from .stringifiers import *

# useful top-level functions to get started quickly
roll = Roller().roll
parse = ast.parser.parse
