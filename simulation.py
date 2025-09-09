import pygame
import random
import sys
from collections import defaultdict

from config import *
from robot import Robot
from grid import Grid

# Functions here run at every simulation step
class Simulation:
    def __init__(self):
        self.grid = Grid()
        self.robots = []
        for i in range(ROBOTS_PER_TEAM):
            self.robots.append(Robot(random.randint(0,3), random.randint(0,3), 0, self.grid.deposits[0]))
            self.robots.append(Robot(random.randint(GRID_SIZE-4,GRID_SIZE-1), random.randint(GRID_SIZE-4,GRID_SIZE-1), 1, self.grid.deposits[1]))
        self.grid.update_robots_positions(self.robots)
        self.scores = {0:0,1:0} # team_id:score (0:Red, 1:Blue)
        self.messages = [] # dicts with keys: from, team, type, pos

    # Main logic for each simulation step
    def step(self): # Runs at each simulation step
        decisions = {} # Robot_id : action
        sensed_store = {} # Robot_id : sensed dict
        self.messages = [] # Clear messages each turn
        for r in self.robots:
            sensed = r.sense(self.grid)
            sensed_store[r.id] = sensed
            for pos,info in sensed.items():
                if info['gold']>0:
                    self.messages.append({'from':r.id,'team':r.team,'type':'gold','pos':pos})
                    break
        for r in self.robots: # We can ingnore this since we are not using messages yet
            r.messages = [m for m in self.messages if m['team']==r.team]

        for r in self.robots:
            decisions[r.id] = r.decide(sensed_store[r.id], self.grid)

        # Trun actions
        for r in self.robots:
            act = decisions[r.id]
            if act == 'turn_left':
                r.facing = (r.facing - 1) % 4
                r.last_action = 'turn_left'
            elif act == 'turn_right':
                r.facing = (r.facing + 1) % 4
                r.last_action = 'turn_right'

        # Plan moves
        move_intents = {}
        for r in self.robots:
            if decisions[r.id] == 'move':
                dx,dy = DIR_VECT[r.facing]
                nx,ny = wrap_pos(r.x+dx,r.y+dy)
                r.planned_move = (nx,ny)
                move_intents[r.id] = (nx,ny)
            else:
                r.planned_move = None

        # Cooperative check for partners
        id_to_robot = {r.id:r for r in self.robots}
        for r in self.robots:
            if r.carrying and r.partner_id is not None:
                partner = id_to_robot.get(r.partner_id)
                if partner and partner.planned_move != r.planned_move:
                    r.planned_move = (r.x,r.y)
                    partner.planned_move = (partner.x, partner.y)
                    print(f"WAIT: Robots {r.id} & {partner.id} waiting to align moves")

        # Execute moves
        for r in self.robots:
            if r.planned_move:
                r.x,r.y = r.planned_move
            r.history.add((r.x,r.y))

        # Hadle pickups
        pickup_attempts = defaultdict(lambda: defaultdict(list))
        for r in self.robots:
            if decisions[r.id] == 'pickup':
                robots_here = self.grid.robots_at((r.x,r.y))
                same_team = [rb for rb in robots_here if rb.team==r.team and not rb.carrying]
                if len(same_team)==2:
                    pickup_attempts[(r.x,r.y)][r.team].append(same_team)
        for pos,teams in pickup_attempts.items():
            for team, pairs_list in teams.items():
                for pair in pairs_list:
                    gold_here = self.grid.gold.get(pos,0)
                    if gold_here>=1:
                        a,b = pair
                        a.carrying = b.carrying = True
                        a.partner_id = b.id; b.partner_id = a.id
                        self.grid.gold[pos] -= 1
                        if self.grid.gold[pos]<=0: del self.grid.gold[pos]
                        print(f"SUCCESS: Robots {a.id} & {b.id} from team {'Red' if team==0 else 'Blue'} picked up gold at {pos}")

        # Hadle deposites
        for r in list(self.robots):
            if r.carrying and (r.x,r.y)==r.deposit:
                partner = id_to_robot.get(r.partner_id)
                if partner and partner.carrying and partner.team==r.team and (partner.x,partner.y)==(r.x,r.y):
                    r.carrying = partner.carrying = False
                    r.partner_id = partner.partner_id = None
                    self.scores[r.team] += 1
                    print(f"DEPOSIT SUCCESS: Robots {r.id} & {partner.id} from team {'Red' if r.team==0 else 'Blue'} deposited gold at {r.deposit}")

        self.grid.update_robots_positions(self.robots)

    # Draw pygame stuff
    def draw(self, screen):
        screen.fill(WHITE)
        for gx in range(GRID_SIZE):
            for gy in range(GRID_SIZE):
                rect = pygame.Rect(gx*CELL_SIZE, gy*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, BLACK, rect, 1)
        for team,pos in self.grid.deposits.items():
            dx,dy = pos
            pygame.draw.rect(screen, DEPOSIT_COL, (dx*CELL_SIZE+2, dy*CELL_SIZE+2, CELL_SIZE-4, CELL_SIZE-4))
        for (x,y),count in self.grid.gold.items():
            for i in range(min(count,4)):
                gx = x*CELL_SIZE+4+i*6
                gy = y*CELL_SIZE+4
                pygame.draw.rect(screen, YELLOW, (gx,gy,8,8))
            if count>4:
                font = pygame.font.SysFont(None,16)
                txt = font.render(str(count),True,BLACK)
                screen.blit(txt,(x*CELL_SIZE+CELL_SIZE-14,y*CELL_SIZE+CELL_SIZE-14))
        for r in self.robots:
            cx = r.x*CELL_SIZE+CELL_SIZE//2
            cy = r.y*CELL_SIZE+CELL_SIZE//2
            color = DARK_RED if (r.team==0 and r.carrying) else (DARK_BLUE if (r.team==1 and r.carrying) else (RED if r.team==0 else BLUE))
            pygame.draw.circle(screen,color,(cx,cy),CELL_SIZE//3)
            if r.carrying:
                pygame.draw.rect(screen,YELLOW,(cx-8,cy-6,16,6))
            font = pygame.font.SysFont(None,14)
            txt = font.render(str(r.id),True,BLACK)
            screen.blit(txt,(cx-6,cy-6))
        font = pygame.font.SysFont(None,24)
        scr = font.render(f"Scores - Red: {self.scores[0]}   Blue: {self.scores[1]}",True,BLACK)
        screen.blit(scr,(8,8))
