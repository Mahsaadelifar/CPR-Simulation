import random
from config import DIR_VECT, BASE_SENSE, wrap_pos, rotate90

class Robot:
    next_id = 0
    def __init__(self, x, y, team, deposit):
        self.id = Robot.next_id; Robot.next_id += 1
        self.x = x
        self.y = y
        self.team = team
        self.deposit = deposit
        self.facing = random.choice([0,1,2,3])
        self.carrying = False
        self.partner_id = None
        self.history = set(); self.history.add((x,y))
        self.messages = []
        self.last_action = 'wait'
        self.planned_move = None
    
    # Returns a dict of sensed info at x,y based on the heading and the vision range
    def sense(self, grid):
        """Return dict of sensed info at nearby cells"""
        rel = []
        for p in BASE_SENSE:
            rp = p
            for _ in range(self.facing):
                rp = rotate90(rp)
            rel.append(rp)
        sensed = {}
        for dx,dy in rel:
            sx,sy = wrap_pos(self.x+dx,self.y+dy)
            sensed[(sx,sy)] = {
                'gold': grid.gold.get((sx,sy),0), # Number of gold pieces
                'deposit': (sx,sy) in grid.deposits.values(), # Is it a deposit?
                'robots': [r.id for r in grid.robots_at((sx,sy))] # list of Robots present
            }
        return sensed

    # Used in decide() to determine action towards a destination
    def action_based_on_destination(self, dest):
        tx,ty = dest
        dx = tx - self.x
        dy = ty - self.y
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
    
    # Decide next action based on sensed info
    def decide(self, sensed, grid):
        if self.carrying and (self.x,self.y)==self.deposit:
            return 'deposit'

        if grid.gold.get((self.x,self.y),0) > 0:
            robots_here = grid.robots_at((self.x,self.y))
            same = [r for r in robots_here if r.team==self.team and not r.carrying]
            other = [r for r in robots_here if r.team!=self.team and not r.carrying]
            if len(same) == 2 and len(other)==0: # This the part we need to develop more
                return 'pickup'

        if self.carrying:
            return self.action_based_on_destination(self.deposit)

        # Prefer unvisited in front
        fx,fy = DIR_VECT[self.facing]
        nx,ny = wrap_pos(self.x+fx, self.y+fy)
        if (nx,ny) not in self.history:
            return 'move'

        # Move toward sensed gold
        gold_positions = [pos for pos,info in sensed.items() if info['gold']>0]
        if gold_positions:
            best = min(gold_positions, key=lambda p: abs(p[0]-self.x)+abs(p[1]-self.y))
            return self.action_based_on_destination(best)

        # Explore neighboring unvisited cells
        neigh = []
        for d in range(4):
            vx,vy = DIR_VECT[d]
            cx,cy = wrap_pos(self.x+vx,self.y+vy)
            if (cx,cy) not in self.history:
                neigh.append((d,(cx,cy)))
        if neigh:
            dtarget,_ = random.choice(neigh)
            if dtarget==self.facing:
                return 'move'
            else:
                diff = (dtarget - self.facing) % 4
                return 'turn_right' if diff==1 else 'turn_left'

        return random.choice(['move','turn_left','turn_right','wait'])
