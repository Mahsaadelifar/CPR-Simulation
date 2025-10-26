import random
from config import *

class Tile:
    def __init__(self, position: list, deposit: bool = False, gold: int = 0):
        self.position = position      # [x,y]
        self.deposit = deposit        # True if this tile is a deposit/base
        self.gold = gold              # Amount of gold on this tile
        self.robots = []              # List of robot objects at that tile

        self.gold_acquirable = False      # two robots need to pickup gold for it to be acquired
    
    def set_deposit(self):
        """Mark this tile as a deposit location."""
        self.deposit = True
    
    def add_gold(self):
        """Add one piece of gold to this tile."""
        self.gold += 1

    def remove_gold(self):
        """Remove one piece of gold (if available)."""
        if self.gold > 0:
            if self.gold_acquirable == True:
                self.gold -= 1
                self.gold_acquirable = False
            self.gold_acquirable = True
        else:
            #raise ValueError("No gold on this tile.")
            print("No gold on this tile.")
    
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

class Grid:
    def __init__(self):
        self.tiles = {} # {(x,y): Tile}
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
        
        for pos in [(0,0), (GRID_SIZE-1, GRID_SIZE-1)]:
            self.tiles[pos].set_deposit()

        self.robots = [] # Robots currently on the grid
        self.scores = {Team.RED: 0, Team.BLUE: 0}

    def add_robot(self, robot, pos):
        """Add a robot to the grid."""
        self.robots.append(robot)
        self.tiles[pos].add_robot(robot)
    
    def add_score(self, team: Team):
        """Add one point to the team's score."""
        self.scores[team] += 0.5 # 1 for each robot's deposit

    def check_gold(self):
        for robot in self.robots:
            if robot.carrying and robot.partner and (robot.pos != robot.partner.pos):
                print(f"DROPPED GOLD: robot {robot.id} and robot {robot.partner.id} dropped gold at {robot.pos}")
                self.tiles[tuple(robot.pos)].add_gold()
                robot.partner.carrying = False
                robot.partner.partner = None
                robot.carrying = False
                robot.partner = None

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