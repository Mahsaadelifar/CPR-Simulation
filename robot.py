import random
from config import DIR_VECT, BASE_SENSE
from base import *

class Robot:
    next_id = 0
    def __init__(self, position: Position, team: Team, deposit: Position):
        self.id = Robot.next_id; Robot.next_id += 1
        self.position = position
        self.team = team
        self.deposit = deposit # Deposite based on team
        self.facing = random.choice([0,1,2,3]) # Random initial direction
        self.carrying = False
        self.partner_id = None
        self.partner = None
        self.history = set(); self.history.add(position.get_tuple())
        self.messages = []
        self.near = [] #list of robots within line of sight for the robot at the current timestep, should get updated at every timestep
        self.last_action = 'wait'
        self.planned_move = None
        self.timestep = 0 #robot keeps track of current time
    
    
    def sense(self, grid):
        """
        Return dict of sensed info at nearby cells.
        Robots can detect gold, deposits, and other robots. ALSO UPDATES SELF.NEAR
        """
        rel = [] # View of sight for each robot based on its facing
        for p in BASE_SENSE:
            rp = p
            for _ in range(self.facing):
                rp = rotate90(rp)
            rel.append(rp)

        sensed = {}
        near = set() #use set to avoid repeats

        for dx,dy in rel:
            sx,sy = wrap_pos(self.position.x+dx,self.position.y+dy)
            tile = grid.tiles[(sx,sy)]
            robots_at_position = [r for r in grid.robots_at((sx,sy))]
            sensed[(sx,sy)] = {
                'gold': tile.gold,                     # Gold count
                'deposit': tile.deposit,               # Is deposit
                'robots': [r.id for r in robots_at_position]
            }

            for robot in robots_at_position:
                near.add(robot)

    
        self.near = list(near)

        return sensed

    def action_based_on_destination(self, dest):
        """
        Decide movement direction towards a destination.
        Returns: 'move', 'turn_left', 'turn_right', or 'wait'
        """
        self.timestep += 0 #increment timsetep by 1 every time the robot decides on a movement

        if isinstance(dest, Position):
            tx, ty = dest.x, dest.y
        else:  # if already a tuple
            tx, ty = dest
        dx = tx - self.position.x
        dy = ty - self.position.y
        # dx>0 means deposit is to the right | dy>0 means deposit is downwards | 0=N, 1=E, 2=S, 3=W
        if abs(dx) > abs(dy):
            desired = 1 if dx>0 else 3
        elif dy!=0:
            desired = 2 if dy>0 else 0
        else:
            return 'wait' # We are already at destination
        if desired == self.facing:
            return 'move'
        else:
            diff = (desired - self.facing) % 4
            return 'turn_right' if diff==1 else 'turn_left'
    
    def decide(self, sensed, grid):
        """
        Decide next action based on sensed environment and current state.
        """

        # Deposit gold if carrying and at base
        if self.carrying and self.position == self.deposit:
            self.partner = None #moved from simulation.py to here to decentralise
            self.partner_id = None
            self.carrying = False
            return 'deposit'

        # Try to pick up gold if on a gold tile with teammate
        if grid.tiles[self.position.get_tuple()].gold > 0:
            robots_here = grid.robots_at(self.position)
            same = [r for r in robots_here if r.team==self.team and not r.carrying]
            other = [r for r in robots_here if r.team!=self.team and not r.carrying]
            if (len(same)>= 2 and len(other)<= 1 and grid.tiles[self.position.get_tuple()].gold >= 1) or (len(same) >= 2 and len(other) >= 2 and grid.tiles[self.position.get_tuple()].gold >= 2):
                self.partner = [r for r in same if not self] #partner is the other robot at the tile
                self.carrying = True
                return 'pickup'
        
        # Carrying? head home
        if self.carrying:
            return self.action_based_on_destination(self.deposit)

        # Prefer unvisited forward cell
        fx,fy = DIR_VECT[self.facing]
        nx,ny = wrap_pos(self.position.x+fx, self.position.y+fy)
        if (nx,ny) not in self.history:
            return 'move'

        # Move toward nearest sensed gold
        gold_positions = [pos for pos,info in sensed.items() if info['gold']>0]
        if gold_positions:
            best = min(gold_positions, key=lambda p: abs(p[0]-self.position.x)+abs(p[1]-self.position.y))
            return self.action_based_on_destination(best)

        # Explore neighboring unvisited cells
        neigh = []
        for d in range(4): # Check all 4 directions
            vx,vy = DIR_VECT[d]
            cx,cy = wrap_pos(self.position.x+vx,self.position.y+vy)
            if (cx,cy) not in self.history:
                neigh.append((d,(cx,cy)))
        if neigh:
            dtarget,_ = random.choice(neigh)
            if dtarget==self.facing:
                return 'move'
            else:
                diff = (dtarget - self.facing) % 4
                return 'turn_right' if diff==1 else 'turn_left'
            
        # Default random action
        return random.choice(['move','turn_left','turn_right','wait'])
    
    def decide_final(self,sensed,grid): #finalised decide which takes into account the partner

        self_planned_action = self.decide(sensed,grid)

        #if robot has no partner
        if self.partner == None:
            return self_planned_action

        else:

            self.send_message_to_near('partner_movement', self_planned_action)

            partner_planned_action, _ = self.process_messages() #process messsages returns two things, only want the first thing

            #compare self and partner planned action
            if partner_planned_action is None:
                return 'wait'

            if partner_planned_action == self_planned_action:
                return self_planned_action

            else:
                return 'wait'
        

            
            
    def send_message_to_near(self,message_type, content=None):
        for robot in self.near: #send message to robots near the robot at the current timestep
            if robot.team != self.team:
                continue
        
            msg_type = "partner_movement" if robot == self.partner else "team_movement"
            msg_content = self.planned_move if content is None else content #can send special messages but by default message is the planned move


            message = {
                'from_team': self.team,
                'from_robot': self.id,
                'type': msg_type,
                'content': msg_content,
                'timestamp': self.timestep,
            }

            robot.messages.append(message)

    def process_messages(self):
        partner_move = None
        teammate_moves = {}


        for message in self.messages:
            msg_type = message['type']
            content = message['content']
            sender = message['from_robot']

            if msg_type == 'partner_movement':
                partner_move = content
            if msg_type == 'team_movement':
                teammate_moves[sender] = content
        
        self.messages.clear() #clear messages list every time it's processed
        return partner_move, teammate_moves
    











        
        