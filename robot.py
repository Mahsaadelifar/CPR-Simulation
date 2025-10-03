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
message_types = {0: "moving_to", 2: "please_help", 4: "im_helping", 5: "partnered", 8: "pickup_gold", 9: "deposit_gold"}

class Message:
    def __init__(self, id: int, content: str, timer: int, proposer: 'Robot', acceptor: 'Robot'):
        self.id = id                # 3 digits; in the format of "timestep, timestep, type"
        self.content = content      # (x,y)
        self.timer = timer          # counts down to when message can be read, i.e. has been sent to all relevant robots
        self.proposer = proposer    # robot who sent the message
        self.acceptor = acceptor    # robot who accepts the message

class KB:
    def __init__(self, deposit):
        self.deposit = deposit  # deposit tile
        self.sensed = {}        # {tile: [object(s)]}
        self.received_messages = {message: [] for message in message_types.values()}  # messages received (but not read); {message_type: [Message, ...]}
        self.read_messages = {message: [] for message in message_types.values()}  # messages read; {message_type: [Message, ...]}
    
    def receive_message(self, message: Message):
        self.received_messages[message.id[2]].append(message)
    
    def read_message(self):
        for mtype, messages in self.received_messages.items():
            if messages:
                msg = messages.pop(0)
                if msg.timer == 0:
                    self.read_messages[mtype].append(msg)

class Robot:
    next_id = 1

    def __init__(self, grid: Grid, team: Team, position: list, direction: Dir, deposit: list, timer: int=0):
      self.grid = grid
      self.id = Robot.next_id; Robot.next_id += 1
      self.team = team
      self.pos = position # [x,y]
      self.dir = direction
      self.timer = timer
      self.planned_move = None
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
        new_x = self.pos[0] + DIR_VECT[self.dir][0]
        new_y = self.pos[1] + DIR_VECT[self.dir][1]
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.grid.tiles[tuple(self.pos)].remove_robot(self)
            self.pos = [new_x, new_y]
            self.grid.tiles[tuple(self.pos)].add_robot(self)
        else:
            pass
