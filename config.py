from enum import Enum

class Team(Enum):
    RED = 0
    BLUE = 1

class Dir(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

# Values
GRID_SIZE = 5
CELL_SIZE = 45
SCORES_HEIGHT = 30
X_WINDOW_SIZE = GRID_SIZE * CELL_SIZE
Y_WINDOW_SIZE = GRID_SIZE * CELL_SIZE + SCORES_HEIGHT
FPS = 2
ROBOTS_PER_TEAM = 4
GOLDS = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 60, 60)
DARK_RED = (139, 0, 0)
BLUE = (60, 120, 200)
DARK_BLUE = (0, 0, 139)
YELLOW = (255, 215, 0)
DEPOSIT_COL = (100, 200, 100)

class ANSI(Enum):
    RESET = "\u001b[0m"
    RED = "\u001b[31m"
    GREEN = "\u001b[32m"
    YELLOW = "\u001b[33m"
