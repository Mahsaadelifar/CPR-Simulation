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

    def get_tuple(self):
        """Return the (x, y) coordinate of the tile."""
        return (self.position.x, self.position.y)
    
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

def turn_cw(sense):
    """Turn (robot's senses) clockwise."""
    x,y = sense
    return (y,-x)

def turn_ccw(sense):
    """Turn (robot's senses) counterclockwise"""
    x, y = sense
    return (-y,x)