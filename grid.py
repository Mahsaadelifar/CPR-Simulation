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
            x,y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            self.tiles[(x, y)].add_gold()
        
        # Set deposit locations (Team based)
        self.tiles[(0, 0)].set_deposit() # RED
        self.tiles[(GRID_SIZE - 1, GRID_SIZE - 1)].set_deposit() # BLUE
        
        self.robots = [] # Robots currently on the grid

    def add_robot(self, robot):
        """Add a robot to the grid."""
        self.robots.append(robot)

