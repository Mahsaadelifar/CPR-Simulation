import random
from config import GRID_SIZE, GOLDS
from base import *

class Grid:
    def __init__(self):
        self.tiles = {}
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                self.tiles[(x, y)] = Tile(position=(x, y))
        
        # Place gold randomly on the grid
        for _ in range(GOLDS):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            self.tiles[(x, y)].add_gold()
        
        # Set deposit locations
        self.tiles[(0, 0)].set_deposit()
        self.tiles[(GRID_SIZE - 1, GRID_SIZE - 1)].set_deposit()
        
        self._robots = []

    def add_robot(self, robot):
        self._robots.append(robot)

    def robots_at(self, position):
        return [r for r in self._robots if r.position == position]

    def update_robots_positions(self, robots):
        self._robots = robots