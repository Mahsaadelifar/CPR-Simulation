import random
from config import GRID_SIZE, GOLDS

class Grid:
    def __init__(self):
        self.gold = {}
        for _ in range(GOLDS):
            x,y = random.randint(0,GRID_SIZE-1), random.randint(0,GRID_SIZE-1)
            self.gold[(x,y)] = self.gold.get((x,y),0)+1
        self.deposits = {0:(0,0),1:(GRID_SIZE-1,GRID_SIZE-1)}
        self._robots = []

    # Add Robot object to _robots list
    def add_robot(self, robot):
        self._robots.append(robot)

    # Returns list of Robot objects at position pos
    def robots_at(self,pos):
        return [r for r in self._robots if (r.x,r.y)==pos]

    # Update internal robot list _robots
    def update_robots_positions(self, robots):
        self._robots = robots
