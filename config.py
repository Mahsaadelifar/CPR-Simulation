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
GRID_SIZE = 20
CELL_SIZE = 45
SCORES_HEIGHT = 30
X_WINDOW_SIZE = GRID_SIZE * CELL_SIZE
Y_WINDOW_SIZE = GRID_SIZE * CELL_SIZE + SCORES_HEIGHT
FPS = 2
ROBOTS_PER_TEAM = 10
GOLDS = 50

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 60, 60)
DARK_RED = (139, 0, 0)
BLUE = (60, 120, 200)
DARK_BLUE = (0, 0, 139)
YELLOW = (255, 215, 0)
DEPOSIT_COL = (100, 200, 100)

# Facing: 0=N, 1=E, 2=S, 3=W (in Pygame (0,0) is top-left; y increases downwards; x increases rightwards)
DIR_VECT = {Dir.NORTH:(0,-1), Dir.EAST:(1,0), Dir.SOUTH:(0,1), Dir.WEST:(-1,0)}

# Relative sensing positions (in (0,0) facing north)
BASE_SENSE = [(-1,-1),(0,-1),(1,-1),(-2,-2),(-1,-2),(0,-2),(1,-2),(2,-2)]
