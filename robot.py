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
    - "restriction": (x,y)
            declaration that a cell is restricted (and should not be entered into/stayed in)
    - "unrestriction": (x,y)
            declaration that a cell is unrestricted (and can be entered into/stayed in)

Partner message types:
    - "facing_direction": Dir
            declaration that the proposer is facing direction Dir
    - "move_forward": Bool
            request for partner to move forward
    - "pickup_req": t_sync
    - "pickup_ack": t_sync
    - "deposit_gold"
    - "sync_proposal": dict of {t_sync: int, plan: list, confirmed: bool, current_step: int}
            proposer proposes a coordinated move plan to take the pair from their current position to the deposit *once they are oriented in the same way*
    - "sync_ack": Bool
            proposer sends in response to a sync proposal to let partner know plan is acknowledged
"""

message_types = ["please_help", "partnered", "restriction", "unrestriction"]
partner_message_types = ["facing_direction", "move_forward", "pickup_req", "pickup_ack", "deposit_gold", "sync_proposal", "sync_ack"]

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
                if message.timestep <= (timestep - 20):
                    messages.remove(message)
        for mtype, messages in self.read_partner_messages.items():
            for message in messages:
                if message.timestep <= (timestep - 20):
                    messages.remove(message)

    def clean_help_requests(self):
        for request in self.read_messages["please_help"]:
            for restriction in self.read_messages["restriction"]:
                if request.content == restriction.content: 
                    if request in self.read_messages["please_help"]: # not sure why there's an error about the request NOT being in the messages list; had to add this
                        self.read_messages["please_help"].remove(request)

    def clean_pickup(self):
        self.read_partner_messages["pickup_req"] = []
        self.read_partner_messages["pickup_ack"] = []

    def clean_kb(self, timestep):
        self.clean_old_messages(timestep)
        self.clean_help_requests()

    def remove_restrictions(self):
        if len(self.read_messages["unrestriction"]) == 0 or len(self.read_messages["restriction"]) == 0:
            return
        else:
            for u_coords in self.read_messages["unrestriction"]:
                for r_coords in self.read_messages["restriction"]:
                    if r_coords.content == u_coords.content:
                        if r_coords in self.read_messages["restriction"]: 
                            self.read_messages["restriction"].remove(r_coords)
                        if u_coords in self.read_messages["unrestriction"]: # in case it was removed before
                            self.read_messages["unrestriction"].remove(u_coords)

    def check_restriction(self, coordinates):
        if len(self.read_messages["restriction"]) != 0:
            for r_coords in self.read_messages["restriction"]:
                if r_coords.content == coordinates:
                    return True
        return False

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

      self.pending_sync = None       # {t_sync: int, plan: list, confirmed: bool, current_step: int}
      self.synced_plan = None        # plan ready to execute
      self.sync_proposer = False

      self.pickup_proposed = False     # proposed pickup
      self.pickup_t_sync = None        # int; timestep

    ### HELPER FUNCTIONS ###

    def next_position(self):
        new_x = self.pos[0] + DIR_VECT[self.dir][0]
        new_y = self.pos[1] + DIR_VECT[self.dir][1]
        if new_x < 0 or new_x >= GRID_SIZE or new_y < 0 or new_y >= GRID_SIZE:
            return self.pos
        return (new_x, new_y)

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

    def reset_pickup(self):
        self.pickup_t_sync = None
        self.pickup_proposed = False
        self.clean_pickup()
        return
    
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
                self.send_restriction() # tell otehrs we already have a partner
                print(ANSI.MAGENTA.value + f"Robot {self.id} successfully partnered with Robot {teammates[0].id}" + ANSI.RESET.value)  
            #no affirmative reply
            else:
                print(ANSI.RED.value + f"Robot {self.id} waiting to partner with Robot {teammates[0].id}" + ANSI.RESET.value)
                #maybe we should send to a different robot??
        else:
            print("No available teammates for Robot {self.id}")

    def pickup_gold(self):
        tile = self.grid.tiles[tuple(self.pos)]
        tile_robots, tile_teammates, tile_gold = self.sense_current_tile()

        if len(tile_teammates) > 1:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: More than two robots in the cell!" + ANSI.RESET.value)
            self.reset_pickup()
            return
        if not self.partner:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No partner to pick up gold with!" + ANSI.RESET.value)
            self.reset_pickup()
            return
        if self.carrying:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Already carrying gold!" + ANSI.RESET.value)
            self.reset_pickup()
            return
        if tile_gold == 0:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No gold to pick up!" + ANSI.RESET.value)
            self.reset_pickup()
            return

        if self.partner.decision[0] != "pickup_gold":
            print(ANSI.RED.value + f"ERROR Robot {self.id} isn't in sync with its partner!" + ANSI.RESET.value)
            self.reset_pickup()
            return

        if self.timestep == self.pickup_t_sync: # successful pickup
            self.carrying = True
            tile.remove_gold()
            self.reset_pickup()
            print(ANSI.MAGENTA.value + f"Robot {self.id} successfully picked up gold at {self.pos}!" + ANSI.RESET.value)
            self.send_unrestriction()
            return
        else:
            self.reset_pickup()
            print(ANSI.RED.value + f"Robot {self.id} failed to pick up gold at {self.pos}!" + ANSI.RESET.value)

    def plan_pickup(self):
        if self.pickup_t_sync:
            if self.pickup_t_sync <= self.timestep:
                print(ANSI.MAGENTA.value + f"Robot {self.id} can't fulfil pickup at timestep {self.pickup_t_sync}!" + ANSI.RESET.value)
                self.reset_pickup()
                return
            else:
                print(ANSI.YELLOW.value + f"Robot {self.id} waiting to pickup gold at timestep {self.pickup_t_sync}!" + ANSI.RESET.value)
                return
        if self.id < self.partner.id: # lesser ID
            pickup_ack_t = self.kb.read_partner_messages.get("pickup_ack")[-1].content if self.kb.read_partner_messages.get("pickup_ack") else None
            if pickup_ack_t: # acknowledgement of a pickup request from partner exists
                if self.timestep < pickup_ack_t:
                    self.pickup_t_sync = pickup_ack_t
                    print(ANSI.YELLOW.value + f"Robot {self.id} acknowledges pickup at timestep {self.pickup_t_sync}!" + ANSI.RESET.value)
                    return
                else:
                    print(ANSI.MAGENTA.value + f"Robot {self.id} can't fulfil pickup at timestep {self.pickup_t_sync}!" + ANSI.RESET.value)
                    self.reset_pickup()
                    return
            elif self.pickup_proposed == False: # no acknowledgement of a pickup request from partner; pickup request not proposed
                t_sync = self.timestep + 10
                self.send_pickup_request(t_sync)
                self.pickup_proposed = True
                print(ANSI.MAGENTA.value + f"Robot {self.id} proposed a pickup request!" + ANSI.RESET.value)
                return
            else:
                print(ANSI.MAGENTA.value + f"Robot {self.id} waiting for a pickup acknowledgement!" + ANSI.RESET.value)
                return
        else: # higher ID
            pickup_req_t = self.kb.read_partner_messages.get("pickup_req")[-1].content if self.kb.read_partner_messages.get("pickup_req") else None
            if pickup_req_t: # pickup request from partner exists
                if self.timestep < pickup_req_t:
                    self.send_pickup_acknowledgement(pickup_req_t)
                    self.pickup_t_sync = pickup_req_t
                    print(ANSI.MAGENTA.value + f"Robot {self.id} acknowledges pickup at timestep {self.pickup_t_sync}!" + ANSI.RESET.value)
                    return
                else:
                    print(ANSI.MAGENTA.value + f"Robot {self.id} can't fulfil pickup at timestep {self.pickup_t_sync}!" + ANSI.RESET.value)
                    self.reset_pickup()
                    return
            else:
                print(ANSI.MAGENTA.value + f"Robot {self.id} waiting for a pickup request!" + ANSI.RESET.value)
                return

    def deposit_gold(self):
        if not self.partner:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: No partner...? How'd you get this far??" + ANSI.RESET.value)
        if not self.carrying:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Not carrying gold!" + ANSI.RESET.value)
        if self.pos != self.kb.deposit:
            print(ANSI.RED.value + f"ERROR Robot {self.id}: Not at deposit point!" + ANSI.RESET.value)
        
        self.carrying = False
        self.partner = None
        self.pending_sync = None       
        self.synced_plan = None 
        self.grid.add_score(self.team)

    def set_target(self):
        help_requests = self.kb.read_messages.get("please_help", [])
        gridrobots, gridteammates, gridgold = self.sense_current_tile()

        if len(gridteammates) > 1 and self.partner == None and self.kb.read_messages["restriction"]:
            for message in self.kb.read_messages.get("restriction"):
                if self.pos == message.content:
                    self.target_position = (0,0) # just get outta there
                    return

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

    def clean_pickup(self):
        self.kb.clean_pickup()

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
        message.countdown = random.randint(1,3)
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
    
    def send_restriction(self):
        """Send a message to all that a cell is restricted"""
        message = Message(timestep=self.timestep, mtype="restriction", content=tuple(self.pos))
        self.send_to_all(message)

    def send_unrestriction(self):
        """Send a message to all that a cell is unrestricted"""
        message = Message(timestep=self.timestep, mtype="unrestriction", content=tuple(self.pos))
        self.send_to_all(message)
    
    def send_help_request(self):
        """Send a please_help message to all robots."""
        message = Message(timestep=self.timestep, mtype="please_help", content=tuple(self.pos))
        self.send_to_all(message)
    
    def send_pickup_request(self, t_sync):
        """Send a pickup_req message to partner."""
        message = Message(timestep=self.timestep, mtype="pickup_req", content=t_sync)
        self.send_to_partner(message)

    def send_pickup_acknowledgement(self, t_sync):
        """Send a pickup_ack message to partner."""
        message = Message(timestep=self.timestep, mtype="pickup_ack", content=t_sync)
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

    def calculate_moves_to_deposit(self):
        #function that returns a list of actions taking robots from current position to deposit

        #need to make a copy of these functions in here cause I don't want to edit the ones outside and break our code
        #since the ones outside take in the robot object itself

        def copy_calc_target_dir(from_pos,to_pos):
            fx,fy = from_pos
            tx,ty = to_pos
            dx = tx-fx
            dy = ty-fy

            if dx != 0:
                return Dir.EAST if dx > 0 else Dir.WEST
            elif dy != 0:
                return Dir.SOUTH if dy > 0 else Dir.NORTH
            else:
                return None
        
        def copy_turn_toward(curr_dir, target_dir):
            dir_order = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
            curr_index = dir_order.index(curr_dir)
            cw_dir = dir_order[(curr_index + 1)%4]
            ccw_dir = dir_order[(curr_index - 1)%4]

            if target_dir == curr_dir:
                return "wait"
            elif target_dir == cw_dir:
                return "turn_cw"
            elif target_dir == ccw_dir:
                return "turn_ccw"
            else:
                return "turn_cw" 
        
        def copy_move_forward(pos,dir): #use to perform moves forward so next move can be calculated
            x,y = pos
            if dir == Dir.NORTH and y>0:
                y -= 1
            elif dir == Dir.SOUTH and y < GRID_SIZE - 1:
                y += 1
            elif dir == Dir.EAST and x < GRID_SIZE - 1:
                return (x + 1, y)
            elif dir == Dir.WEST and x > 0:
                return (x - 1, y)
            return (x,y)
        
        #loop to simulate all the moves
        pos = self.pos
        dir = self.dir
        target = self.kb.deposit
        moves = []

        #fix the movement so it moves all the way in x direction first then in y direction
        for axis in [0,1]: #0 is x, 1 is y
            while pos[axis] != target[axis]:
                if axis ==0:
                    target_dir = Dir.EAST if target[0] > pos[0] else Dir.WEST
                else:
                    target_dir = Dir.SOUTH if target[1] > pos[1] else Dir.NORTH
                
                if dir != target_dir:
                    move = copy_turn_toward(dir, target_dir)
                    moves.append(move)
                
                    dirs = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST]
                    dir = dirs[(dirs.index(dir) + (1 if move=="turn_cw" else -1)) % 4]
                else:
                    moves.append("move_forward")
                    pos = copy_move_forward(pos, dir)
        moves.append("deposit_gold")
        #return statement below!!!



        # while pos != target:
        #     #print(f"current position: {pos}, current target: {target}")
        #     target_dir = copy_calc_target_dir(pos,target)

        #     if target_dir is None:
        #         break

        #     if dir != target_dir:
        #         move = copy_turn_toward(dir,target_dir)
        #         moves.append(move)

        #         if move == "turn_cw":
        #             dir = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST][([Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST].index(dir) + 1) % 4]
        #         elif move == "turn_ccw":
        #             dir = [Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST][([Dir.NORTH, Dir.EAST, Dir.SOUTH, Dir.WEST].index(dir) - 1) % 4]
        #     else:
        #         moves.append("move_forward")
        #         pos = copy_move_forward(pos,dir)

        return moves

    def propose_sync_plan(self,timestep):
        #propose move with partner including all timstep actions
        plan_delay = 10 #how many timesteps into the future the robots plan to move together
        #can change plan delay later, maybe see if larger/smaller values would work better
        #10 seems to be a pretty decent value so far

        if not self.partner:
            return
        
        t_sync = timestep + plan_delay
        plan = self.calculate_moves_to_deposit()

        sync_message = Message(
        timestep=timestep,
        mtype="sync_proposal",
        content=(t_sync, plan),
        proposer=self,
        acceptor=self.partner,
        countdown=random.randint(1, 3) #set a random delay AHHHH
        )

        self.send_to_partner(sync_message)
        self.pending_sync = {"t_sync": t_sync, "plan": plan, "confirmed": False, "current_step": 0}
        self.sync_proposer = True
        print(f"Robot {self.id}: proposed sync plan for timestep {t_sync}: {plan}")

    def handle_sync_messages(self,timestep):
        msgs = self.kb.read_partner_messages

        #handle proposals for sync
        if msgs["sync_proposal"]:
            latest = msgs["sync_proposal"][-1]
            t_sync, plan = latest.content
            proposer = latest.proposer

            if timestep < t_sync:

                ack = Message(
                    timestep=timestep,
                    mtype="sync_ack",
                    content=(t_sync,),
                    proposer=self,
                    acceptor=proposer,
                    countdown=random.randint(1, 3)
                )

                self.send_to_partner(ack)
                self.pending_sync = {"t_sync": t_sync, "plan": plan, "confirmed": True, "current_step":0}
                print(f"Robot {self.id}: accepted sync plan starting at {t_sync}: {plan}")
            
            else:
                print(f"Robot {self.id}: rejected expired plan proposed at (t={t_sync}, now={timestep})")
        
        #responding to partner acknowledgement
        if msgs["sync_ack"]:
            ack = msgs["sync_ack"][-1]
            t_sync = ack.content[0]

            if self.pending_sync and self.pending_sync["t_sync"] == t_sync:
                if timestep < t_sync:
                    self.pending_sync["confirmed"] = True
                    print(f"Robot {self.id}: sync plan confirmed for timestep {t_sync}")
                else:
                    print(f"Robot {self.id}: recieved late ack for t={t_sync}, ignoring")

    def check_restriction(self, coordinates):
        return self.kb.check_restriction(coordinates)

    def remove_restrictions(self):
        self.kb.remove_restrictions() 

###__________________________________________________________________________###

    def plan(self, timestep):
        gridrobots, gridteammates, gridgold = self.sense_current_tile()
        self.set_target()
        self.remove_restrictions()

        if len(gridteammates) > 1 and self.partner == None and len(self.kb.read_messages["restriction"]) != 0:
            for message in self.kb.read_messages.get("restriction"):
                if tuple(self.pos) == message.content:
                    self.decision = [self.next_move_to_target(), tuple(self.pos)]
                    print(ANSI.CYAN.value + f"Robot {self.id} at {self.pos} recognizing it must leave" + ANSI.RESET.value)
                    return

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
                if timestep == self.pickup_t_sync:
                    self.decision = ["pickup_gold", tuple(self.pos)]
                else:
                    self.decision = ["plan_pickup", tuple(self.pos)]
                return

        # DEPOSIT GOLD if carrying and at deposit (already accounted for in the move sync)
        # if self.carrying and (self.pos == self.kb.deposit):
        #     self.decision = ["deposit_gold", tuple(self.pos)]
        #     print(ANSI.CYAN.value + f"Robot {self.id} at {self.pos} depositing gold" + ANSI.RESET.value)
        #     return

        # COORDINATED MOVE if carrying gold with partner
        if self.carrying and self.partner:

            #handling sync messagesfor partners
            self.handle_sync_messages(self.timestep)

            #get orientation of partnered robots to allign

            #handling direction messages
            self.send_direction()
            partner_dir = self.kb.read_partner_messages.get("facing_direction")[-1].content if self.kb.read_partner_messages.get("facing_direction") else None
            target_dir = self.calc_target_dir()

            if not self.synced_plan:
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

                #once this line is reached, both facing the right direction
                if self.carrying and self.partner and not self.synced_plan:
                    #propose a synced movement plan
                    if not self.pending_sync:
                        if self.partner and self.id < self.partner.id: #robot with lower ID always the sync proposer
                            self.propose_sync_plan(self.timestep)

                    #if a plan is already confirmed, go for it
                    elif self.pending_sync["confirmed"] and self.timestep == self.pending_sync["t_sync"]:
                        self.synced_plan = self.pending_sync
                        self.pending_sync = None
                        print(f"Robot {self.id}: activating sync plan at timestep {self.timestep}")
                
            #if already executing a synced plan, check the plan for what to do
            if self.synced_plan:
                plan = self.synced_plan
                step_index = plan["current_step"]
                planned_step_timestep = plan["t_sync"] + step_index
                move = plan["plan"][step_index]
                print(f"robot: {self.id} current timestep: {self.timestep}, planned_step_timestep:{planned_step_timestep}, move: {move}")
                if self.timestep == planned_step_timestep:
                    #move = plan["plan"][step_index]
                    self.decision = [move, tuple(self.pos)]
                    plan["current_step"] += 1
                    return
                else:
                    self.decision = ["wait", tuple(self.pos)]
                    return

        # if all else fails just do what you want
        if not (self.carrying and self.partner):
            next_move = self.next_move_to_target()
            print(ANSI.YELLOW.value + f"Robot {self.id} recognizes {self.next_position()}'s restriction is {self.check_restriction(self.next_position())}" + ANSI.RESET.value)
            if self.check_restriction(self.next_position()) and next_move == "move_forward":
                print(ANSI.CYAN.value + f"Robot {self.id} at {self.pos} recognizing it can't enter cell {self.next_position()}" + ANSI.RESET.value)
                self.decision = ["wait", tuple(self.pos)]
            else:
                self.decision = [next_move, tuple(self.pos)]
            return
        else:
            self.decision = ["wait", tuple(self.pos)]

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
        
        elif self.decision[0] == "plan_pickup":
            self.plan_pickup()
            
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
            
        
        
     

