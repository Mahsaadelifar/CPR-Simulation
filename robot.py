import random
import math
from config import *
from base import *

"""
Message types:
    - "please_help": (x,y)
            request for nearby robots to come to (x,y)
    - "partnered": (x,y)
            acknowledgement that proposer is partnered with acceptor
    - "partner_unneeded": (x,y)

Partner message types:
    - "facing_direction": Dir
            declaration that the proposer is facing direction Dir
    - "move_forward": Bool
            request for partner to move forward
    - "pickup_gold": (x,y)
"""

message_types = ["please_help", "partnered", "partner_unneeded"]
partner_message_types = ["facing_direction", "move_forward", "pickup_gold", "deposit_gold"]

class Message:
    def __init__(self, timestep: int, mtype: str, content: tuple, proposer: 'Robot'=None, acceptor: 'Robot'=None, countdown: int=1):
        self.timestep = timestep    # timestep when message was sent
        self.mtype = mtype          # message type
        self.content = content      # (x,y)
        self.countdown = countdown  # counts down to when message can be read, e.g. in the next timestep
        self.proposer = proposer    # robot who sent the message
        self.acceptor = acceptor    # robot who accepts the message
    
    def __eq__(self, other):
        return ((abs(self.timestep - other.timestep) < 5) and
                self.mtype == other.mtype and
                self.content == other.content and
                self.proposer == other.proposer and
                self.acceptor == other.acceptor)
    
    def copy(self):
        return Message(timestep=self.timestep, mtype=self.mtype, content=self.content, proposer=self.proposer, acceptor=self.acceptor, countdown=self.countdown)

    def decrement_countdown(self):
        if self.countdown > 0:
            self.countdown -= 1

class KB:
    def __init__(self, deposit):
        self.deposit = deposit  # deposit tile
        self.sensed = {}        # {tile: [object(s)]}
        
        self.received_messages = {mtype: [] for mtype in message_types}                   # messages received (but not read); {message_type: [Message, ...]}
        self.read_messages = {mtype: [] for mtype in message_types}                       # messages read; {message_type: [Message, ...]}
        
        self.received_partner_messages = {pmtype: [] for pmtype in partner_message_types} # partner messages received (but not read); {message_type: [Message, ...]}
        self.read_partner_messages = {pmtype: [] for pmtype in partner_message_types}     # partner messages read; {message_type: [Message, ...]}
    
    def receive_message(self, message: Message):
        if message.mtype not in message_types: # partner messages
            if message not in self.received_partner_messages[message.mtype]:
                self.received_partner_messages[message.mtype].append(message.copy()) # stores a copy, so that countdown can be delayed
        else: # regular messages
            if message not in self.received_messages[message.mtype]:
                self.received_messages[message.mtype].append(message.copy())
    
    def deliver_messages(self):
        for mtype, messages in self.received_messages.items():
            for message in messages:
                message.decrement_countdown()
        for pmtype, messages in self.received_partner_messages.items():
            for message in messages:
                message.decrement_countdown()

    def read_message(self):
        for mtype, messages in self.received_messages.items():
            for message in messages:
                if message.countdown == 0:
                    self.read_messages[mtype].append(message)
                    messages.remove(message)
                message.decrement_countdown()
        for pmtype, messages in self.received_partner_messages.items():
            for message in messages: 
                if message.countdown == 0:
                    self.read_partner_messages[pmtype].append(message) # only keep the latest partner message
                    messages.remove(message)
                message.decrement_countdown()
    
    def clean_old_messages(self, timestep):
        for mtype, messages in self.read_messages.items():
            for message in messages:
                if message.timestep <= (timestep - 10):
                    messages.remove(message)
        for mtype, messages in self.read_partner_messages.items():
            for message in messages:
                if message.timestep <= (timestep - 10):
                    messages.remove(message)

    def clean_help_requests(self):
        for request in self.read_messages["please_help"]:
            for confirmation in self.read_messages["partner_unneeded"]:
                if request.content == confirmation.content: 
                    #should we also add a check for if the sender is the same? 
                    # cause mutliple robots can send help messages from the same location 
                    # and the content is the location
                    if request in self.read_messages["please_help"]: # not sure why there's an error about the request NOT being in the messages list; had to add this
                        self.read_messages["please_help"].remove(request)

    def clean_kb(self, timestep):
        self.clean_old_messages(timestep)
        self.clean_help_requests()
   
class Robot:
    next_id = 1

    def __init__(self, grid: Grid, team: Team, position: list, direction: Dir, deposit: list, timestep: int = 0):
      self.grid = grid
      self.id = Robot.next_id; Robot.next_id += 1
      self.team = team
      self.pos = position # [x,y]
      self.dir = direction
      self.kb = KB(deposit = deposit) # !!! might have a better way to keep track of this
      self.timestep = timestep # current timestep

      self.carrying = False # True if carrying gold
      self.decision = None # [decision, position]
      self.target_position = None # (x,y); the target position the robot is heading to

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
        dx = self.target_position[0] - self.pos[0]
        dy = self.target_position[1] - self.pos[1]

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
            if tile: #and (self.pos[0]+dx, self.pos[1]+dy) not in self.kb.sensed: commented out so it writes over old info
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

    def turn(self, turn_dir): # turn cw or ccw
        dir_order = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
        curr_index = dir_order.index(self.dir)

        if turn_dir == "cw":
            self.dir = dir_order[(curr_index + 1) % 4]
        elif turn_dir == "ccw":
            self.dir = dir_order[(curr_index - 1) % 4]
        else:
            raise ValueError("Not a valid turn direction!")

    def turn_toward(self, target_direction):
        if self.dir == target_direction:
            return "wait"
        
        # if not facing the right direction, TURN!!!
        dir_order = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
        curr_index = dir_order.index(self.dir) # index of current direction
        cw_dir = dir_order[(curr_index + 1) % 4]
        ccw_dir  = dir_order[(curr_index - 1) % 4]

        if target_direction == ccw_dir:
            return "turn_ccw"
        else:
            return "turn_cw"

    def move(self):
        """Move forward in the direction it's facing."""
        new_x, new_y = self.next_position()
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.grid.tiles[tuple(self.pos)].remove_robot(self)
            self.pos = [new_x, new_y]
            self.grid.tiles[tuple(self.pos)].add_robot(self)
        else:
            pass

    def pair_up(self, teammates, gold): # teammates is a list of teammates on the grid, gold is number of gold on the grid
        if self.partner is None and (len(teammates) > 0):
            self.send_partner_request(teammates[0])
            #if recieved an affirmative response, pair up
            if self.kb.read_messages.get("partnered") and self.kb.read_messages.get("partnered")[-1].proposer.id == teammates[0].id: #are we allowed to access teammates.id??
                self.partner = teammates[0]
                self.send_partner_unneeded() #tell otehrs we already have a partner
                print(ANSI.MAGENTA.value + f"Robot {self.id} successfully partnered with Robot {teammates[0].id}" + ANSI.RESET.value)  
            #no affirmative reply
            else:
                print(ANSI.RED.value + f"Robot {self.id} waiting to partner with Robot {teammates[0].id}" + ANSI.RESET.value)
                #maybe we should send to a different robot??
        else:
            print("no available teammates for robot {self.id}")
                
    def pickup_gold(self):
        tile = self.grid.tiles[tuple(self.pos)]
        tile_robots, tile_teammates, tile_gold = self.sense_current_tile()
        
        if not self.partner:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No partner to pick up gold with!" + ANSI.RESET.value)
        if self.carrying:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Already carrying gold!" + ANSI.RESET.value)
        if tile_gold == 0:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No gold to pick up!" + ANSI.RESET.value)
        # if self.kb.sensed.get(tuple(self.pos), {}).get("gold", 0) == 0:
        #     print(ANSI.RED.value + f"ERROR Robot {self.id}: No gold to pick up!" + ANSI.RESET.value)

        self.send_pickup_request()
        pickup_confirmation = self.kb.read_partner_messages.get("pickup_gold")[-1].content if self.kb.read_partner_messages.get("pickup_gold") else None
        if pickup_confirmation and tile_gold >0:
            self.carrying = True
            tile.remove_gold()
            print(ANSI.MAGENTA.value + f"Robots {self.id} and {self.partner.id} successfully picked up gold at {self.pos}" + ANSI.RESET.value)
        else:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No gold to pick up!" + ANSI.RESET.value)
        return

    def deposit_gold(self):
        if not self.partner:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No partner...? How'd you get this far??" + ANSI.RESET.value)
        if not self.carrying:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Not carrying gold!" + ANSI.RESET.value)
        if self.pos != self.kb.deposit:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Not at deposit point!" + ANSI.RESET.value)
        
        self.send_deposit_request()
        deposit_confirmation = self.kb.read_partner_messages.get("deposit_gold")[-1].content if self.kb.read_partner_messages.get("deposit_gold") else None
        if deposit_confirmation:
            self.carrying = False
            self.partner = None
            self.grid.add_score(self.team)


    def set_target(self):
        help_requests = self.kb.read_messages.get("please_help", [])

        # if you have a partner and gold, then your target is the deposit
        if self.carrying and (self.partner != None):
            self.target_position = tuple(self.kb.deposit)
            return

        # otherwise, respond to help requests
        elif help_requests:
            help_message = help_requests[0] # currently selecting first help message recieved, should ideally loop through and select the closest message
            if self.calc_dist(self.pos, help_message.content) < 5:
                self.target_position = tuple(help_message.content)
                return
    
        else:
            if self.closest_gold(): # if nothing else to do, target is closest gold
                self.target_position = tuple(self.closest_gold())
            else:  # if no gold in sight
                self.target_position = self.next_position()
                
                if self.target_position == self.pos:
                    x, y = self.pos

                    # default to current coordinates
                    new_x, new_y = x, y

                    if x == 0:
                        new_x = GRID_SIZE - 1
                    elif x == GRID_SIZE - 1:
                        new_x = 0

                    if y == 0:
                        new_y = GRID_SIZE - 1
                    elif y == GRID_SIZE - 1:
                        new_y = 0

                    self.target_position = (new_x, new_y)


                


    
    def next_move_to_target(self):
        target_dir = self.calc_target_dir()
        if self.dir == target_dir:
            return "move_forward"
        return self.turn_toward(target_dir)
    
    ### MESSAGE ACTIONS ###

    def clean_kb(self, timestep):
        """Clean knowledge base"""
        self.kb.clean_kb(timestep)

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

    def send_to_partner(self, message: Message):
        """Send a message to the partner robot."""
        if self.partner:
            self.send_message(message, self.partner)
        else:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No partner to send message to!" + ANSI.RESET.value)

    def send_partner_request(self, acceptor: 'Robot'):
        """Send a partnered message to the acceptor robot."""
        message = Message(timestep=self.timestep, mtype="partnered", content=tuple(self.pos)) # content is the position, but we only need to check for proposer/acceptor
        self.send_message(message, acceptor)
    
    def send_partner_unneeded(self):
        """Send a message to all that a partner is no longer needed"""
        message = Message(timestep=self.timestep, mtype="partner_unneeded", content=tuple(self.pos))
        self.send_to_all(message)
    
    def send_help_request(self):
        """Send a please_help message to all robots."""
        message = Message(timestep=self.timestep, mtype="please_help", content=tuple(self.pos))
        self.send_to_all(message)
    
    def send_pickup_request(self):
        """Send a pickup_gold message to partner."""
        message = Message(timestep=self.timestep, mtype="pickup_gold", content=tuple(self.pos))
        self.send_to_partner(message)

    def send_deposit_request(self):
        """Send a deposit_gold message to partner."""
        message = Message(timestep=self.timestep, mtype="deposit_gold", content=tuple(self.pos))
        self.send_to_partner(message)

    def send_direction(self):
        """Send a facing_direction message to partner."""
        message = Message(timestep=self.timestep, mtype="facing_direction", content=self.dir)
        self.send_to_partner(message)
    
    def send_move_request(self):
        """Send a move_forward message to partner."""
        message = Message(timestep=self.timestep, mtype="move_forward", content=tuple(self.pos))
        self.send_to_partner(message)

###__________________________________________________________________________###

    def plan(self):
        gridrobots, gridteammates, gridgold = self.sense_current_tile()
        self.set_target()

        # if standing on gold
        if gridgold > 0:
            # SEND HELP REQUEST (no other teammates)
            if not self.partner and len(gridteammates) == 0:
                self.decision = ["wait", tuple(self.pos)]
                self.send_help_request()
                print(ANSI.CYAN.value + f"Robot {self.id} at {self.pos} sending help request" + ANSI.RESET.value)
                return
            # PAIR UP (has teammates, no partner)
            if not self.partner and len(gridteammates) > 0:
                self.decision = ["pair_up", tuple(self.pos)]
                print(ANSI.MAGENTA.value + f"Robot {self.id} is attempting to pair up" + ANSI.RESET.value)
                return
            # PICKUP GOLD (has partner, not carrying)
            if not self.carrying and self.partner != None:
                self.decision = ["pickup_gold", tuple(self.pos)]
                print(ANSI.MAGENTA.value + f"Robot {self.id} and {self.partner.id} at {self.pos} picking up gold" + ANSI.RESET.value)
                return

        # DEPOSIT GOLD if carrying and at deposit
        if self.carrying and (self.pos == self.kb.deposit):
            self.decision = ["deposit_gold", tuple(self.pos)]
            print(ANSI.CYAN.value + f"Robot {self.id} at {self.pos} depositing gold" + ANSI.RESET.value)
            return

        # COORDINATED MOVE if carrying gold with partner
        if self.carrying and self.partner:
            self.send_direction()
            partner_dir = self.kb.read_partner_messages.get("facing_direction")[-1].content if self.kb.read_partner_messages.get("facing_direction") else None
            target_dir = self.calc_target_dir()

            # TURN if not facing the right direction
            if self.dir != target_dir: # if not facing the right direction, turn to face the right direction
                self.decision = [self.turn_toward(target_dir), tuple(self.pos)]
                self.send_direction() #send new direction after turning
                print(ANSI.YELLOW.value + f"Robot {self.id} is turning direction to {self.dir.name}" + ANSI.RESET.value)
                return
            
            # we are currently facing the right direction
            # WAIT if partner not facing the right direction (calculated best direction to head to deposit from current position)
            if partner_dir != target_dir: # wait for partner before each move
                self.decision = ["wait", tuple(self.pos)]
                print(ANSI.YELLOW.value + f"Robot {self.id} is waiting for teammate to turn direction to {self.dir.name}" + ANSI.RESET.value)
                self.send_move_request() #send move request if we are facing the right direction
                self.send_direction()
                return
            
            # MOVE if both facing the right direction
            self.send_move_request()
            move_confirmation = None 

            #reads most recent move confirmation in read_partner_messages list
            if len(self.kb.read_partner_messages.get("move_forward")) > 0:
                move_confirmation = self.kb.read_partner_messages.get("move_forward")[-1].content if self.kb.read_partner_messages.get("move_forward") else None
                print(f"Robot {self.id} has the move confirmation: {move_confirmation} sent at timestep {self.kb.read_partner_messages.get("move_forward")[-1].timestep}")

            #if in the previous timestep partner was ready to move
            if move_confirmation and move_confirmation == tuple(self.pos):
                self.decision = ["move_forward", tuple(self.pos)]
            else: #if partner was not ready to move in previous timestep
                self.decision = ["wait", tuple(self.pos)]
            print(ANSI.BLUE.value + f"Robot {self.id} and {self.partner.id} are moving forward to the {self.dir.name}" + ANSI.RESET.value)
            return


        # if all else fails just do what you want
        self.decision = [self.next_move_to_target(), tuple(self.pos)]
        return

    # Updated execute with coordinated move and prints
    def execute(self, timestep):
        tile = self.grid.tiles[tuple(self.pos)]
        gridrobots, gridteammates, gridgold = self.sense_current_tile()
        
        self.clean_kb(timestep)

        if self.partner:
            print(ANSI.GREEN.value + 
                f"robot: {self.id}, partner: {self.partner.id}, target: {self.target_position}, decision: {self.decision}, position: {self.pos}, team_deposit: {self.kb.deposit}" +
                ANSI.RESET.value)
        else:
            print(ANSI.GREEN.value + 
                f"robot: {self.id}, partner: None, target: {self.target_position}, decision: {self.decision}, position: {self.pos}, team_deposit: {self.kb.deposit}" +
                ANSI.RESET.value)

        if self.decision[0] == "move_forward":
            self.move()
            self.sense()
            
        elif self.decision[0] == "pickup_gold":
            self.pickup_gold()

        elif self.decision[0] == "wait":
            pass

        elif self.decision[0] == "turn_ccw":
            self.turn("ccw")
            self.sense()
        
        elif self.decision[0] == "turn_cw":
            self.turn("cw")
            self.sense()
        
        elif self.decision[0] == "deposit_gold":
            self.deposit_gold()
        
        elif self.decision[0] == "pair_up":
            self.pair_up(gridteammates, gridgold)
            
        
        
     

