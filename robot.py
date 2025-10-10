import random
import math
from config import *
from base import *
from grid import *

"""
Message types:
    - "moving_to": proposer is moving to (x,y)
    - "please_help": request for nearby robots to come to (x,y)
    - "im_helping": acknowledgement that proposer is going to help at (x,y)
    - "partnered": acknowledgement that proposer is partnered with acceptor at (x,y)
    - "pickup_gold": request for partner to pick up gold at (x,y)
    - "deposit_gold": request for partner to deposit gold at (x,y)
"""

message_types = {"0": "moving_to", "2": "please_help", "4": "im_helping", "5": "partnered", "8": "pickup_gold", "9": "deposit_gold"}

class Message:
    def __init__(self, id: str, content: tuple, proposer: 'Robot'=None, acceptor: 'Robot'=None, countdown: int=(ROBOTS_PER_TEAM-1)):
        self.id = id                # 4 digits; in the format of "timestep, timestep, timestep, type"
        self.content = content      # (x,y)
        self.countdown = countdown  # counts down to when message can be read, i.e. has been sent to all relevant robots !!! WILL NEED TO FIX
        self.proposer = proposer    # robot who sent the message
        self.acceptor = acceptor    # robot who accepts the message

class KB:
    def __init__(self, deposit):
        self.deposit = deposit  # deposit tile
        self.sensed = {}        # {tile: [object(s)]}
        self.received_messages = {mtype: [] for mtype in message_types.values()}  # messages received (but not read); {message_type: [Message, ...]}
        self.read_messages = {mtype: [] for mtype in message_types.values()}  # messages read; {message_type: [Message, ...]}
    
    def receive_message(self, message: Message):
        if message not in self.received_messages.get(message_types[message.id[-1]]) and message not in self.read_messages.get(message_types[message.id[-1]]):
            self.received_messages[message_types[message.id[-1]]].append(message)
    
    def read_message(self): # !!! WILL NEED TO FIX
        for mtype, messages in self.received_messages.items():
            for message in messages[:]:
                if message.countdown <= 1:
                    self.read_messages[mtype].append(message) # throws a copy of the message into read_messages
                    self.received_messages[mtype].remove(message) # removes message from received_messages
                else:
                    message.countdown -= 1
        
class Robot:
    next_id = 1

    def __init__(self, grid: Grid, team: Team, position: list, direction: Dir, deposit: list):
      self.grid = grid
      self.id = Robot.next_id; Robot.next_id += 1
      self.team = team
      self.pos = position # [x,y]
      self.dir = direction
      self.kb = KB(deposit = deposit) # !!! might have a better way to keep track of this

      self.carrying = False # True if carrying gold
      self.decision = None # [decision, position]
      self.target_position = None # [x,y]; the target position the robot is heading to

      self.partner = None # the robot it is partnered with

    ### HELPER FUNCTIONS ###

    def next_position(self):
        new_x = self.pos[0] + DIR_VECT[self.dir][0]
        new_y = self.pos[1] + DIR_VECT[self.dir][1]
        if new_x < 0 or new_x >= GRID_SIZE or new_y < 0 or new_y >= GRID_SIZE:
            return self.pos
        return [new_x, new_y]

    def calc_dist(self, a, b): # axis_dist(self, a,b): #a and b are tuples (x1,y1) and (x2,y2)
        return round(math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2), 2)

    def closest_gold(self):
        gold_positions = [pos for pos, info in self.kb.sensed.items() if info.get("gold", 0) > 0]
        if gold_positions == []:
            return None
        
        closest_gold_pos = min(gold_positions, key=lambda pos: self.calc_dist(tuple(self.pos), pos))
        return closest_gold_pos

    def calc_target_dir(self):
        dx = self.target[0] - self.pos[0]
        dy = self.target[1] - self.pos[1]

        if abs(dx) > abs(dy):
            target_dir = Dir.EAST if dx > 0 else Dir.WEST
        else:
            target_dir = Dir.SOUTH if dy > 0 else Dir.NORTH
        
        return target_dir
    
    ### ROBOT ACTIONS ###

    def sense(self): # !!! not really working!!!!!
        """Sense the surrounding tiles and update KB."""
        tile = self.grid.tiles[tuple(self.pos)]
        self.kb.sensed[tuple(self.pos)] = {"deposit": tile.deposit, "gold": tile.gold, "robots": tile.robots}

        for dx,dy in SENSE_VECT[self.dir]:
            tile = self.grid.tiles[(self.pos[0]+dx, self.pos[1]+dy)] if (self.pos[0]+dx, self.pos[1]+dy) in self.grid.tiles else None
            if tile and (self.pos[0]+dx, self.pos[1]+dy) not in self.kb.sensed:
                objects = {}
                objects["deposit"] = tile.deposit 
                objects["gold"] = tile.gold
                objects["robots"] = tile.robots
                self.kb.sensed[(self.pos[0]+dx, self.pos[1]+dy)] = objects

    def sense_current_tile(self): # sense_tile_values(self):
        robots = self.kb.sensed.get(tuple(self.pos)).get("robots", [])
        teammates = [robot for robot in robots if (robot != self and robot.team == self.team)]
        gold = self.kb.sensed.get(tuple(self.pos)).get("gold", 0)

        return (robots, teammates, gold)

    def turn(self, turn_dir): # turn left or right
        dir_order = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
        curr_index = dir_order.index(self.dir)

        if turn_dir == "right":
            self.dir = dir_order[(curr_index + 1) % 4]
        elif turn_dir == "left":
            self.dir = dir_order[(curr_index - 1) % 4]
        else:
            raise ValueError("you can only turn left or right girl")

    def turn_toward(self, target_direction):
        if self.dir == target_direction:
            return "wait"
        
        # if not facing right direction, TURN!!!
        dir_order = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
        curr_index = dir_order.index(self.dir) # index of current direction
        right_dir = dir_order[(curr_index + 1) % 4]
        left_dir  = dir_order[(curr_index - 1) % 4]

        if target_direction == left_dir:
            return "turn_left"
        else:
            return "turn_right"

    def move(self):
        """Move forward in the direction it's facing."""
        new_x, new_y = self.next_position()
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.grid.tiles[tuple(self.pos)].remove_robot(self)
            self.pos = [new_x, new_y]
            self.grid.tiles[tuple(self.pos)].add_robot(self)
        else:
            pass

    def pair_up(self, gridteammates, gridgold): # grid robots is a list of teammates on the grid, gridgold is number of gold on the grid
        if (len(gridteammates) == 1) and (gridgold> 0): # if we DO have a partner and gold at the tile is greater than 0
            self.partner = gridteammates[0]
    
    def pickup_gold(self):
        if self.partner and not self.carrying and (self.kb.sensed.get(tuple(self.pos), {}).get("gold", 0) > 0):
            tile = self.grid.tiles[tuple(self.pos)]
            tile.remove_gold()
            self.carrying = True
            self.partner.carrying = True
            return
        elif not self.partner:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No partner to pick up gold with!" + ANSI.RESET.value)
        elif self.kb.sensed.get(tuple(self.pos), {}).get("gold", 0) == 0:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No gold to pick up!" + ANSI.RESET.value)
        else:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Unaccounted error for picking up gold!" + ANSI.RESET.value)

    def deposit_gold(self):
        if self.carrying and (self.pos == self.kb.deposit):
            self.carrying = False
            if self.partner:
                self.partner.carrying = False
                self.partner = None
        else:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Not carrying gold or not at deposit!" + ANSI.RESET.value)

    def set_target(self):
        help_requests = self.kb.read_messages.get("please_help", [])

        # if you have a partner and gold, then your target is the deposit
        if self.carrying and (self.partner != None):
            self.target = tuple(self.kb.deposit)

        # otherwise, respond to help requests
        elif help_requests:
            help_message = help_requests[0] # currently selecting first help message recieved, should ideally loop through and select the closest message
            self.target = help_message.content
            return
    
        else:
            if self.closest_gold(): # if nothing else to do, target is closest gold
                self.target = self.closest_gold()
            else: # if no gold in sight move forward 1
                self.target = self.next_position()
    
    def next_move_to_target(self):
        target_dir = self.calc_target_dir()
        if self.dir == target_dir:
            return "move_forward"
        return self.turn_toward(target_dir)
    
    ### MESSAGE ACTIONS ###

    def receive_message(self, message: Message):
        """Receive a message and store it in the KB."""
        self.kb.receive_message(message)
    
    def read_message(self):
        """Read received messages in the KB."""
        self.kb.read_message()

    def send_message(self, message: Message, acceptor: 'Robot'):
        """Send a message to a robot."""
        message.proposer = self
        message.acceptor = acceptor
        acceptor.receive_message(message)

    def send_to_all(self, message: Message):
        """Send a message to all robots (within the same team) on the grid."""
        for robot in self.grid.robots:
            if robot != self and robot.team == self.team:
                self.send_message(message, robot)
   
#__________________________________________________________________________

    def plan(self):
        gridrobots, gridteammates, gridgold = self.sense_current_tile()
        self.set_target()

        # Deposit gold if carrying and at deposit
        if self.carrying and (self.pos == self.kb.deposit):
            self.decision = ["deposit_gold", tuple(self.pos)]
            print(ANSI.CYAN.value + f"Robot {self.id} at {self.pos} depositing gold" + ANSI.RESET.value)
            return
        
        if self.carrying and self.partner and self.partner.carrying and (tuple(self.pos) != self.kb.deposit): # Coordinated move if carrying gold
            if self.dir != self.calc_target_dir(): # if not facing the right direction, turn to face the right direction
                self.decision = [self.turn_toward(self.calc_target_dir()), tuple(self.pos)]
                print(ANSI.YELLOW.value + f"Robot {self.id} turning to face deposit at {self.kb.deposit}" + ANSI.RESET.value)
                return
            if self.partner.dir != self.calc_target_dir() or self.partner.decision[0] == "turn_left" or self.partner.decision[0] == "turn_right": # wait for partner before each move
                self.decision = ["wait", tuple(self.pos)]
                print(ANSI.BLUE.value + f"Robot {self.id} and {self.partner.id} waiting to coordinate direction to {self.dir.name}" + ANSI.RESET.value)
                return
            self.decision = [self.next_move_to_target(), tuple(self.pos)]
            print(ANSI.BLUE.value + f"Robot {self.id} and {self.partner.id} coordinated move direction set to {self.dir.name}" + ANSI.RESET.value)
            return

        if not self.carrying and (gridgold > 0): # If not carrying and there is gold at the tile
            if self.partner: # Pickup gold if possible
                self.decision = ["pickup_gold", tuple(self.pos)]
                print(ANSI.MAGENTA.value + f"Robot {self.id} and {self.partner.id} at {self.pos} picking up gold" + ANSI.RESET.value)
                return
            else: # Pair up with a teammate if possible
                self.decision = ["pair_up", tuple(self.pos)]
                print(ANSI.MAGENTA.value + f"Robot {self.id} partnering up" + ANSI.RESET.value)
                return

        # if all else fails just do what you want
        self.decision = [self.next_move_to_target(), tuple(self.pos)]
        return

    # Updated execute with coordinated move and prints
    def execute(self):
        tile = self.grid.tiles[tuple(self.pos)]
        gridrobots, gridteammates, gridgold = self.sense_current_tile()

        if self.partner:
            print(ANSI.GREEN.value + 
                f"robot: {self.id}, partner: {self.partner.id}, target: {self.target}, decision: {self.decision}, position: {self.pos}, team_deposit: {self.kb.deposit}" +
                ANSI.RESET.value)
        else:
            print(ANSI.GREEN.value + 
                f"robot: {self.id}, partner: None, target: {self.target}, decision: {self.decision}, position: {self.pos}, team_deposit: {self.kb.deposit}" +
                ANSI.RESET.value)

        if self.decision[0] == "move_forward":
            self.move()
            self.sense()
            
        elif self.decision[0] == "pickup_gold":
            self.pickup_gold()

        elif self.decision[0] == "wait":
            pass

        elif self.decision[0] == "turn_left":
            self.turn("left")
            self.sense() #sense after turning
        
        elif self.decision[0] == "turn_right":
            self.turn("right")
            self.sense() #sense after turning
        
        elif self.decision[0] == "deposit_gold":
            self.deposit_gold()
        
        elif self.decision[0] == "pair_up":
            self.pair_up(gridteammates, gridgold)
            
        
        
     

