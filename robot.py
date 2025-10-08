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
        self.countdown = countdown  # counts down to when message can be read, i.e. has been sent to all relevant robots
        self.proposer = proposer    # robot who sent the message
        self.acceptor = acceptor    # robot who accepts the message

class KB:
    def __init__(self, deposit):
        self.deposit = deposit  # deposit tile
        self.sensed = {}        # {tile: [object(s)]}
        self.received_messages = {message: [] for message in message_types.values()}  # messages received (but not read); {message_type: [Message, ...]}
        self.read_messages = {message: [] for message in message_types.values()}  # messages read; {message_type: [Message, ...]}
    
    def receive_message(self, message: Message):
        self.received_messages[message_types[message.id[3]]].append(message)
    
    def read_message(self):
        for mtype, messages in self.received_messages.items():
            if messages:
                msg = messages.pop(0) # REMOVES the message from received_messages
                if msg.countdown == 0:
                    self.read_messages[mtype].append(msg) # throws message into read_messages
                else:
                    msg.countdown -= 1 # counts down each time the message is read by a robot (the message is the same entity for all robots)
                    self.received_messages[mtype].append(msg) # puts the message back into received_messages if countdown > 0
        
class Robot:
    next_id = 1

    def __init__(self, grid: Grid, team: Team, position: list, direction: Dir, deposit: list, timer: int=0):
      self.grid = grid
      self.id = Robot.next_id; Robot.next_id += 1
      self.team = team
      self.pos = position # [x,y]
      self.dir = direction
      self.timer = timer
      self.decision = None # [decision, position]
      self.carrying = False
      self.kb = KB(deposit = deposit)

    def sense(self):
        """Sense the surrounding tiles and update KB."""
        for dx,dy in SENSE_VECT[self.dir]:
            tile = self.grid.tiles[(self.pos[0]+dx, self.pos[1]+dy)] if (self.pos[0]+dx, self.pos[1]+dy) in self.grid.tiles else None
            if tile and (self.pos[0]+dx, self.pos[1]+dy) not in self.kb.sensed:
                objects = {}
                objects["deposit"] = tile.deposit
                objects["gold"] = tile.gold
                objects["robots"] = tile.robots
                self.kb.sensed[(self.pos[0]+dx, self.pos[1]+dy)] = objects

    def turn(self, direction):
        """Turn to face a new direction."""
        self.dir = direction

    def move(self):
        """Move forward in the direction it's facing."""
        new_x, new_y = self.next_position()
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.grid.tiles[tuple(self.pos)].remove_robot(self)
            self.pos = [new_x, new_y]
            self.grid.tiles[tuple(self.pos)].add_robot(self)
        else:
            pass

    def receive_message(self, message: Message):
        """Receive a message and store it in the KB."""
        self.kb.receive_message(message)
    
    def read_message(self):
        """Read received messages in the KB."""
        self.kb.read_message()

    def send_message(self, message: Message, acceptor: 'Robot'):
        """Send a message to all robots within a certain range."""
        message.proposer = self
        message.acceptor = acceptor
        acceptor.receive_message(message)

    def send_to_all(self, message: Message):
        """Send a message to all robots (within the same team) on the grid."""
        for robot in self.grid.robots:
            if robot != self and robot.team == self.team:
                self.send_message(message, robot)

    def next_position(self):
        new_x = self.pos[0] + DIR_VECT[self.dir][0]
        new_y = self.pos[1] + DIR_VECT[self.dir][1]
        if new_x < 0 or new_x >= GRID_SIZE or new_y < 0 or new_y >= GRID_SIZE:
            return self.pos
        return [new_x, new_y]
    
    def planned_move(self, timestep):
        if self.decision and self.decision[0] == "moving_to":
            if self.plan(timestep):
                self.move()
            else:
                pass
    
    def plan(self, timestep):
        # CURRENTLY ONLY MOVE!!!!
        for message in self.kb.read_messages["moving_to"]:
            if message.content == tuple(self.next_position()):
                self.decision = ["moving_to", self.pos]
                self.send_to_all(Message(id=f"{timestep}0", content=tuple(self.pos)))
                return False
        self.decision = ["moving_to", self.next_position()] # also includes the position it's STAYING at
        self.send_to_all(Message(id=f"{timestep}0", content=tuple(self.next_position())))
        return True

                