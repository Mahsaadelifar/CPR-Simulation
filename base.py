from config import *

class Tile:
    def __init__(self, position: list, deposit: bool = False, gold: int = 0):
        self.position = position      # [x,y]
        self.deposit = deposit        # True if this tile is a deposit/base
        self.gold = gold              # Amount of gold on this tile
        self.robots = []              # List of robot objects at that tile
    
    def set_deposit(self):
        """Mark this tile as a deposit location."""
        self.deposit = True
    
    def add_gold(self):
        """Add one piece of gold to this tile."""
        self.gold += 1

    def remove_gold(self):
        """Remove one piece of gold (if available)."""
        if self.gold > 0:
            self.gold -= 1
        else:
            raise ValueError("No gold on this tile.")
    
    def add_robot(self, robot):
        """Add a robot onto the tile"""
        if robot not in self.robots:
            self.robots.append(robot)
        else:
            raise ValueError("Robot already on tile!")
    
    def remove_robot(self, robot):
        """Remove a robot off the tile"""
        if robot in self.robots:
            self.robots.remove(robot)
        else:
            raise ValueError("Robot not on tile!")

# Turn clockwise
def turn_cw(vector):
    x,y = vector
    return (-y,x)

# In Pygame (0,0) is top-left; y increases downwards; x increases rightwards)
DIR_VECT = {Dir.NORTH:(0,-1), Dir.EAST:(1,0), Dir.SOUTH:(0,1), Dir.WEST:(-1,0)}

# Relative sensing vectors
NORTH_SENSE = [(-1,-1),(0,-1),(1,-1),(-2,-2),(-1,-2),(0,-2),(1,-2),(2,-2)]
EAST_SENSE = [turn_cw(v) for v in NORTH_SENSE]
SOUTH_SENSE = [turn_cw(v) for v in EAST_SENSE]
WEST_SENSE = [turn_cw(v) for v in SOUTH_SENSE]

SENSE_VECT = {Dir.NORTH: NORTH_SENSE, Dir.EAST: EAST_SENSE, Dir.SOUTH: SOUTH_SENSE, Dir.WEST: WEST_SENSE}