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
        self.received_messages = {mtype: [] for mtype in message_types.values()}  # messages received (but not read); {message_type: [Message, ...]}
        self.read_messages = {mtype: [] for mtype in message_types.values()}  # messages read; {message_type: [Message, ...]}
    
    def receive_message(self, message: Message):
        if message not in self.received_messages[message_types[message.id[-1]]] and message not in self.read_messages[message_types[message.id[-1]]]:
            self.received_messages[message_types[message.id[-1]]].append(message)
    
    def read_message(self):
        for mtype, messages in self.received_messages.items():
            for message in messages[:]:
                if message.countdown <= 1:
                    self.read_messages[mtype].append(message) # throws a copy of the message into read_messages
                    self.received_messages[mtype].remove(message) # removes message from received_messages
                else:
                    message.countdown -= 1
    
    def clean_moving_to_messages(self, timestep):
        self.read_messages["moving_to"] = [message for message in self.read_messages["moving_to"] if message.id[0:3] >= timestep]
        
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
      self.partner_id = None #ID for partner robot carrying gold together
      self.target_position = None # [x,y] target position robot is heading to
      self.kb = KB(deposit = deposit)
      self.partner = None #robot object partner NEED TO FIX CODE SO WE CAN REMOVE THIS
      self.target = None

    def sense(self):
        """Sense the surrounding tiles and update KB."""
        for dx,dy in SENSE_VECT[self.dir]:
            tile = self.grid.tiles[(self.pos[0]+dx, self.pos[1]+dy)] if (self.pos[0]+dx, self.pos[1]+dy) in self.grid.tiles else None
            if tile and (self.pos[0]+dx, self.pos[1]+dy) not in self.kb.sensed:
                objects = {}
                objects["deposit"] = tile.deposit 
                objects["gold"] = tile.gold
                objects["robots"] = tile.robots
                self.kb.sensed[(self.pos[0]+dx, self.pos[1]+dy)] = objects #WHY IS IT NOT SENSING????

    def turn(self, turn_dir): #convert left or right into a specific direction
        dir_order = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
        curr_index = dir_order.index(self.dir)

        if turn_dir == "right":
            self.dir = dir_order[(curr_index + 1) % 4]
        elif turn_dir == "left":
            self.dir = dir_order[(curr_index - 1) % 4]
        else:
            raise ValueError("you can only turn left or right girl'")

    def move(self):
        """Move forward in the direction it's facing."""
        new_x, new_y = self.next_position()
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.grid.tiles[tuple(self.pos)].remove_robot(self)
            self.pos = [new_x, new_y]
            self.grid.tiles[tuple(self.pos)].add_robot(self) #SHOULD THIS BE IN SIMULATION.PY??????
        else:
            pass

    def receive_message(self, message: Message):
        """Receive a message and store it in the KB."""
        self.kb.receive_message(message)
    
    def read_message(self):
        """Read received messages in the KB."""
        self.kb.read_message()

    def send_message(self, message: Message, acceptor: 'Robot'):
        """Send a message to all robots within a certain range.""" #what is that range girl
        message.proposer = self
        message.acceptor = acceptor
        acceptor.receive_message(message)

    def send_to_all(self, message: Message):
        """Send a message to all robots (within the same team) on the grid."""
        for robot in self.grid.robots:
            if robot != self and robot.team == self.team:
                message.acceptor = robot #added to change acceptor to each robot
                self.send_message(message, robot)
    
    def clean_messages(self, timestep):
        self.kb.clean_moving_to_messages(timestep)

    def next_position(self):
        new_x = self.pos[0] + DIR_VECT[self.dir][0]
        new_y = self.pos[1] + DIR_VECT[self.dir][1]
        if new_x < 0 or new_x >= GRID_SIZE or new_y < 0 or new_y >= GRID_SIZE:
            return self.pos
        return [new_x, new_y]
    
    def sense_tile_values(self):
        robots_at_grid = self.kb.sensed.get(tuple(self.pos), {}).get("robots", [])
        teammates_at_grid = [robot for robot in robots_at_grid if robot!=self]
        gold_at_grid = self.kb.sensed.get(tuple(self.pos), {}).get("gold", 0)

        return(robots_at_grid, teammates_at_grid, gold_at_grid)

    def pair_up(self, gridteammates, gridgold): #grid robots is a list of teammates on the grid, gridgold is number og gold on the grid
        if (gridteammates == 1) and (gridgold> 0): #if we DO have a partner and gold at the tile is greater than 0
            self.partner = gridteammates[0]
            self.partner_id = gridteammates[0].id
            self.carrying = True

    
    def axis_dist(self, a,b): #a and b are tuples (x1,y1), (x2, y2)
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def closest_gold(self):
        gold_positions = [
            pos for pos, info in self.kb.sensed.items()
            if info.get("gold", 0) > 0  ]

        if not gold_positions:
            return None
        
        closest = min(gold_positions, key=lambda pos: self.axis_dist(tuple(self.pos), pos))
        return closest


    def set_target(self):
        help_requests = self.kb.read_messages.get("please_help", [])
        #if you have a partner and gold, your target is the deposit
        if self.carrying and (self.partner_id != None):
            self.target = tuple(self.KB.deposit)

        #otherwise, respond to help requests

        elif help_requests:
            help_message = help_requests[0] #currently selecting first help message recieved, should ideally loop through and select the closest message
            self.target = help_message.content

            help_response = Message(
                id = f"{self.timestep}4",
                content = self.target,
                proposer = self,
                acceptor = None #will be set by the send_to_all function later
                )
            
            self.send_to_all(help_response)
            return
    
        
        else:
            #if nothing else to do, target is closest gold
            if self.closest_gold():
                self.target = self.closest_gold()
            
            else: #if no gold in sight move forward 1
                self.target = self.next_position()


    def turn_toward(self, target_direction):
        if self.dir == target_direction:
            return "wait"
        
        #if not facing right direction, TURN!!!
        dir_order = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
        curr_index = dir_order.index(self.dir) #index of current direction
        right_dir = dir_order[(curr_index + 1) % 4]
        left_dir  = dir_order[(curr_index - 1) % 4]

        if target_direction == right_dir:
            return "turn_right"
        elif target_direction == left_dir:
            return "turn_left"
        else:
            # Opposite direction
            return "turn_right"
        


    def next_move_to_target(self):
        #function that decides best next move from these options: move forward, turn right, turn left, deposit
        #based on self.target where self.target is a tuple of coordinates (x,y)

        #deposit at target (maybe don't need here and override it in the plan function)
        if (tuple(self.pos) == self.target) and self.carrying:
            return "deposit"
    
        #diff in dist of each axis
        to_move_x = self.target[0] - self.pos[0]
        to_move_y = self.target[1] - self.pos[1]

        if abs(to_move_x) > abs(to_move_y):
            target_dir = Dir.EAST if to_move_x > 0 else Dir.WEST
        else:
            target_dir = Dir.SOUTH if to_move_y > 0 else Dir.NORTH

        #move if correctly oreintatededded
        if self.dir == target_dir:
            return "move"
        
        return self.turn_toward(target_dir)
        
#__________________________________________________________________________

    def plan(self, timestep):

        self.set_target() 

        #tile = self.grid.tiles[tuple(self.pos)] don't think we're allowed to access it like this it has to come from the robot KB to be decntralised
        gridrobots, gridteammates, gridgold = self.sense_tile_values()

        # Deposit gold if carrying and at deposit
        if self.carrying and (self.position == self.kb.deposit):
            self.decision = ["deposit_gold", tuple(self.pos)]
            print(f"Robot {self.id} at {self.pos} will deposit gold")
            #self.send_to_all(Message(id=f"{timestep}9", content=tuple(self.pos))) should send message AFTER successful execution
            return

        # Pickup gold if partner available
        #same_team_robots = [r for r in tile.robots if r.team == self.team and r != self] 
        self.pair_up(gridteammates,gridgold)
        if self.partner_id != None:
            self.decision = ["pickup_gold", tuple(self.pos)]
            return
        #self.send_to_all(Message(id=f"{timestep}8", content=tuple(self.pos))) should send message AFTER successful execution

        # Coordinated move if carrying gold
        if self.carrying and self.partner and self.partner.carrying and (tuple(self.pos) != self.kb.deposit):
            #have robot with lower ID turn in place so it faces same direction as partner
            if self.dir != self.partner.dir: #STILL NOT IDEAL CAISE WE SHOULDN'T BE ABLE TO SEE PARTNER'S DIRECTION???
                # Lower ID aligns with higher ID
                if self.id < self.partner_id: 
                    self.decision = [self.turn_toward(self.partner.dir), tuple(self.pos)]
                    print(f"Robot {self.id} turning to align with partner {self.partner_id}")
                    return
                else:
                    self.decision = ["wait", tuple(self.pos)]
                    return
                    # higher ID robot waits while partner aligns
            
            #if both robots faced in the same direction, just use usual logic to calculate next move
            self.decision = [self.next_move_to_target(), tuple(self.pos)]
            print(f"Robot {self.id} and {self.partner.id} coordinated move direction set to {self.dir.name}")
            return
    
        #if all else fails just do what you want
        self.decision = [self.next_move_to_target(), tuple(self.pos)]
        return

    # Updated execute with coordinated move and prints
    def execute(self, timestep):
        tile = self.grid.tiles[tuple(self.pos)]

        print(f"target: {self.target}, decision: {self.decision}, position: {self.pos}")
        #print(f"sensed: {self.kb.sensed}")

        if self.decision[0] == "move":
            self.move()
            self.sense() #sense after moving
            # Move normally or coordinated if carrying gold
            # if self.carrying and self.partner and self.partner.carrying:
            #     # Check if partner moving in same direction
            #     #if self.next_position() == self.partner.next_position(): CAN'T CHECK HERE!!!!!! UNLESS WE KNOW NEXT_POSITION FROM MESSAGES
            #     self.move()
            #     print(f"Robot {self.id} and partner {self.partner.id} carried gold to {self.pos}")
            

        elif self.decision[0] == "pickup_gold":
            return "pickup_gold" #already set stuff up in the pair_up() function previously

        elif self.decision[0] == "wait":
            return "wait"

        elif self.decision[0] == "turn_left":
            self.turn("left")
            self.sense() #sense after turning
            return "turn_left"
        
        elif self.decision[0] == "turn_right":
            self.turn("right")
            self.sense() #sense after turning
            return "turn right"
        
        elif self.decision[0] == "deposit":
            self.carrying = False
            self.partner_id = None
            self.partner = None
        
        
        #     # Check robots on the tile and split by team
        #     tile_robots = tile.robots
        #     teams = {Team.RED: [], Team.BLUE: []}
        #     for r in tile_robots:
        #         teams[r.team].append(r)

        #     my_team = self.team
        #     other_team = Team.RED if my_team == Team.BLUE else Team.BLUE

        #     # Normal pickup: exactly 2 from my team, less than 2 from other team
        #     if len(teams[my_team]) == 2 and len(teams[other_team]) < 2:
        #         if tile.gold >= 1 and not self.carrying:
        #             self.carrying = True
        #             partner = [r for r in teams[my_team] if r != self][0]
        #             partner.carrying = True
        #             self.partner = partner
        #             partner.partner = self
        #             tile.gold -= 1
        #             print(f"Robot {self.id} picked up gold with partner {partner.id} at {self.pos}")

        #     # Conflict pickup: 2 from each team
        #     elif len(teams[Team.RED]) == 2 and len(teams[Team.BLUE]) == 2:
        #         if tile.gold >= 2 and not self.carrying:
        #             self.carrying = True
        #             partner = [r for r in teams[my_team] if r != self][0]
        #             partner.carrying = True
        #             self.partner = partner
        #             partner.partner = self
        #             tile.gold -= 1
        #             print(f"Robot {self.id} picked up gold with partner {partner.id} at {self.pos} (conflict pickup)")
        #         elif tile.gold < 2:
        #             print(f"Robot {self.id} failed to pick up gold due to insufficient gold (conflict)")

        #     else:
        #         print(f"Robot {self.id} failed to pick up gold at {self.pos}")
        # elif self.decision[0] == "deposit_gold":
        #     if self.carrying:
        #         self.carrying = False
        #         print(f"Robot {self.id} deposited gold at {self.pos}")
        #         self.partner_id = None
        #         self.send_to_all(Message(id=f"{timestep}9", content=tuple(self.pos)))
        #     else:
        #         print(f"Robots {self.id} and {self.partner_id} tried to deposit gold but was not carrying any")
        #         self.partner_id = None




            

