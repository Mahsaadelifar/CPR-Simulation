import random

# --- CONFIG ---
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
DIR_VECT = {0:(0,-1),1:(1,0),2:(0,1),3:(-1,0)}

# # Make sures x,y are within grid bounds
def wrap_pos(x,y):
    return max(0,min(GRID_SIZE-1,x)), max(0,min(GRID_SIZE-1,y))

# Rotate 90 degrees clockwise
def rotate90(p):
    x,y = p
    return (y,-x)

# Relative sensing positions (in (0,0) facing north)
BASE_SENSE = [(-1,-1),(0,-1),(1,-1),(-2,-2),(-1,-2),(0,-2),(1,-2),(2,-2)]
