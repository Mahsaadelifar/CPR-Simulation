import random
from config import GRID_SIZE, GOLDS
from base import *

class Grid:
    def __init__(self):
        # Create dictionary of all tiles in the grid
        # Key = (x,y), Value = Tile object
        self.tiles = {}
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                self.tiles[(x, y)] = Tile(position=Position(x, y))
        
        # Place gold randomly on the grid
        for _ in range(GOLDS):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            self.tiles[(x, y)].add_gold()
        
        # Set deposit locations (Team based)
        self.tiles[(0, 0)].set_deposit() # RED
        self.tiles[(GRID_SIZE - 1, GRID_SIZE - 1)].set_deposit() # BLUE
        
        self._robots = [] # Robots currently on the grid

    def add_robot(self, robot):
        """Add a robot to the grid."""
        self._robots.append(robot)

    def robots_at(self, position):
        """
        Return list of all robots at a given position.
        Accepts Position object or (x,y) tuple.
        """
        pos_tuple = position.get_tuple() if isinstance(position, Position) else position
        return [r for r in self._robots if r.position.get_tuple() == pos_tuple]

    def update_robots_positions(self, robots):
        """Replace the list of tracked robots with the given list."""
        self._robots = robots