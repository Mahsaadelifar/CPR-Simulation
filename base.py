from enum import Enum
from config import *

class Team(Enum):
    RED = 0
    BLUE = 1

class Position:
    """Represents a grid coordinate (x, y)."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        """Compare two Position objects by x and y values."""
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y

    def get_tuple(self):
        """Return (x, y) tuple form of the position."""
        return (self.x, self.y)

class Tile:
    def __init__(self, position: Position, deposit: bool = False, gold: int = 0):
        self.position = position      # Position object
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

    def get_tuple(self):
        """Return the (x, y) coordinate of the tile."""
        return (self.position.x, self.position.y)
    
    def robot_off_tile(self, robot): #use to add a robot to a tile position
        if robot in self.robots:
            self.robots.remove(robot)
    
    def robot_on_tile(self,robot): #use to remove a robot from a tile position
        if robot not in self.robots:
            self.robots.append(robot)


# Utility functions

def wrap_pos(x,y):
    """
    Ensure (x, y) stays within grid bounds.
    Clamps values to [0, GRID_SIZE-1].
    """
    return max(0,min(GRID_SIZE-1,x)), max(0,min(GRID_SIZE-1,y))

def rotate90(p):
    """
    Rotate a (dx, dy) vector 90 degrees clockwise.
    Example: (0, -1) -> (1, 0)
    """
    x,y = p
    return (y,-x)