import random
from config import DIR_VECT, BASE_SENSE
from base import *

class Message:
    def __init__(self, id: int, content: str, timer: int, proposer: 'Robot', acceptor: 'Robot'):
        self.id = id # timestep, timestep, type
        self.content = content
        self.timer = timer
        self.proposer = proposer
        self.acceptor = acceptor

class KB:
    def __init__(self, deposit):
        self.deposit = deposit
        self.sensed = {} # {tile: [object(s)]} 
        self.messages = {}

class Robot:
    next_id = 1

    def __init__(self, team: Team, position: list, direction: Dir, deposit: list, timer: int=0):
      self.id = Robot.next_id; Robot.next_id += 1
      self.team = team
      self.pos = position # [x,y]
      self.dir = direction
      self.timer = timer
      self.planned_move = None
      self.carrying = False
      self.kb = KB(deposit = deposit)