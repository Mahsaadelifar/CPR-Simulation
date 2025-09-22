from enum import Enum
from config import *

class Team(Enum):
    RED = 0
    BLUE = 1

class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y

    def get_tuple(self):
        return (self.x, self.y)

class Tile:
    def __init__(self, position: Position, deposit: bool = False, gold: int = 0):
        self.position = position
        self.deposit = deposit
        self.gold = gold
    
    def set_deposit(self):
        self.deposit = True
    
    def add_gold(self):
        self.gold += 1

    def remove_gold(self):
        if self.gold > 0:
            self.gold -= 1
        else:
            raise ValueError("No gold on this tile.")

    def get_tuple(self):
        return (self.position.x, self.position.y)

# # Make sures x,y are within grid bounds
def wrap_pos(x,y):
    return max(0,min(GRID_SIZE-1,x)), max(0,min(GRID_SIZE-1,y))

# Rotate 90 degrees clockwise
def rotate90(p):
    x,y = p
    return (y,-x)