import random
from config import GRID_SIZE, GOLDS
from base import *

class Grid:
    def __init__(self):
        self.tiles = {} # Key = (x,y), Value = Tile object
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                self.tiles[(x, y)] = Tile(position=[x,y])
        
        # Place gold randomly on the grid
        for _ in range(GOLDS):
            while True:
                x,y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
                if (x,y) not in [(0, 0), (GRID_SIZE - 1, GRID_SIZE - 1)]:
                    break
            self.tiles[(x,y)].add_gold()
        
        for pos in [(0,0), (GRID_SIZE-1, GRID_SIZE-1)]: # No distinction between teams yet
            self.tiles[pos].set_deposit()

        self.robots = [] # Robots currently on the grid

    def add_robot(self, robot, pos):
        """Add a robot to the grid."""
        self.robots.append(robot)
        self.tiles[pos].add_robot(robot)

