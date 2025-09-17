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

        # Turn actions
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

        # Handle pickups--------------------------------------------------------------------------------------------------------------------
        pickup_attempts = defaultdict(lambda: defaultdict(list))

        #store positions where at least one robot is trying to pick up gold
        pickup_positions = set((r.x,r.y) for r in self.robots if decisions[r.id] == 'pickup')

        #iterate through positions to get robots at each position
        for pos in pickup_positions:
            robots_here = self.grid.robots_at(pos)
            gold_here = self.grid.gold.get(pos,0) #number of gold at the position

            #group robots not carrying anything at the tile by their teams
            team_groups = defaultdict(list) #key is the team, value is the robot object
            for rb in robots_here:
                if decisions[rb.id] == "pickup" and not rb.carrying: #if there are other robots on that square but it's not trying to pick up does the pickup still fail?? cause I don't check for that rn
                    team_groups[rb.team].append(rb)  

            if len(team_groups) ==0:
                continue #no robots at the position

            team_ids = list(team_groups.keys())
            team1_id = team_ids[0]
            team2_id = team_ids[1] if len(team_ids)>1 else None

            team1 = team_groups[team1_id] #get list of robots in team one from the stored info
            team2 = team_groups[team2_id] if team2_id else [] #get list of robots in team two from the stored info

            #case where both teams are there

            if team2_id:
                team1_valid = len(team1) == 2
                team2_valid = len(team2) == 2

                #if both teams valid
                if team1_valid and team2_valid:
                    if gold_here >=2: #if more than 2 gold on the tile
                        pickup_attempts[pos][team1_id].append(tuple(team1))
                        pickup_attempts[pos][team2_id].append(tuple(team2))
                        print(f"PICKUP SUCCESS: both teams {team1_id} (robots {team1}) and {team2_id} (robots {team2}) picked up gold")
                    else:
                        print(f"PICKUP FAILURE: Only {gold_here} gold bar(s) at {pos}, both teams failed to pick up gold")
                
                else: #one or both teams fail to pick up because they don't have two robots picking up gold
                    #should the other team actually succeed if one team has too many/ not enough robots?
                    if team1_valid and not team2_valid and gold_here >= 1:
                            pickup_attempts[pos][team1_id].append(tuple(team1))
                            print(f"PICKUP FAILURE: Team {team2_id} failed pickup at {pos} (has {len(team2)} pickers)")
                    elif team2_valid and not team1_valid and gold_here >= 1:
                            pickup_attempts[pos][team2_id].append(tuple(team2))
                            print(f"PICKUP FAILURE: Team {team1_id} failed pickup at {pos} (has {len(team1)} pickers)")
                    else: #case where both are not valid
                        print(f"PICKUP FAILURE: Both teams failed pickup at {pos}, team {team1_id} has (has {len(team1)} pickers and team {team2_id} (has {len(team2)} pickers)")

            
            #case where only one team is picking up gold
            else:
                if len(team1) == 2:
                    if gold_here >= 1:
                        pickup_attempts[pos][team1_id].append(tuple(team1))
                    else:
                        print(f"PICKUP FAILURE: No gold at {pos}, team {team1_id} fails to pick up gold")
                else:
                    print(f"PICKUP FAILURE: Team {team1_id} failed pickup at {pos} (has {len(team1)} pickers)")

        #at this point, we have a pickup_attempts dict which stores successful pickup attempts at each positions
        #keys are position (x,y), values are a dict where keys are the team id, and values are a list of robot objects from the team

        for pos,teams in pickup_attempts.items():
           gold_here = self.grid.gold.get(pos,0)
           for team_id, pair_list in teams.items():
               for (a,b) in pair_list:
                   if gold_here >=1:
                       a.carrying = b.carrying = True
                       a.partner_id, b.partner_id = b.id, a.id
                       gold_here -= 1
                       self.grid.gold[pos] = gold_here
                       print(f"PICKUP SUCCESS: Robots {a.id} & {b.id} from team {'Red' if team_id ==0 else 'Blue'} picked up gold at {pos}")
                   else:
                       print(f"PICKUP FAILURE: Robots {a.id} & {b.id} from team {'Red' if team_id ==0 else 'Blue'} failed to pickup gold") 
                   

        # Handle deposits -------------------------------------------------------------------------------------
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

        # Draw scores
        pygame.draw.rect(screen, WHITE, (0, 0, X_WINDOW_SIZE, SCORES_HEIGHT))
        font = pygame.font.SysFont(None,24)
        scores = font.render(f"Scores - Red: {self.scores[0]}   Blue: {self.scores[1]}",True,BLACK)
        screen.blit(scores,(8,8))

        # Draw grid
        for gx in range(GRID_SIZE):
            for gy in range(GRID_SIZE):
                rect = pygame.Rect(gx*CELL_SIZE, gy*CELL_SIZE + SCORES_HEIGHT, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, BLACK, rect, 1)

        # Draw deposits
        for team,pos in self.grid.deposits.items():
            dx,dy = pos
            pygame.draw.rect(screen, DEPOSIT_COL, (dx*CELL_SIZE+2, dy*CELL_SIZE + 2 + SCORES_HEIGHT, CELL_SIZE-4, CELL_SIZE-4))

        # Draw gold
        for (x,y),count in self.grid.gold.items():
                font = pygame.font.SysFont(None,16)
                txt = font.render(str(count),True,BLACK)
                cx = x*CELL_SIZE + CELL_SIZE // 2
                cy = y*CELL_SIZE + CELL_SIZE // 2 + SCORES_HEIGHT
                pygame.draw.circle(screen, YELLOW, ((cx, cy)), 8)
                screen.blit(txt, ((cx - txt.get_width() // 2), (cy - txt.get_height() // 2)))
        
        # Draw robots
        robots_by_cell = defaultdict(lambda: {0: [], 1: []}) # Creates dict of robots from each team for each cell
        for r in self.robots:
            robots_by_cell[(r.x, r.y)][r.team].append(r)

        for (x,y), teams in robots_by_cell.items():
            # Red team
            for idx, r in enumerate(teams[0][:2]): # Maximum 2 robots
                if idx == 0: # Top left
                    cx = x * CELL_SIZE + CELL_SIZE // 4
                    cy = y * CELL_SIZE + CELL_SIZE // 4 + SCORES_HEIGHT
                else: # Bottom left
                    cx = x * CELL_SIZE + CELL_SIZE // 4
                    cy = y * CELL_SIZE + 3 * CELL_SIZE // 4 + SCORES_HEIGHT
                color = DARK_RED if r.carrying else RED
                pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 5)
                font = pygame.font.SysFont(None, 14)
                txt = font.render(str(r.id), True, BLACK)
                screen.blit(txt, (cx - 6, cy - 6))
            
            # Blue team
            for idx, r in enumerate(teams[1][:2]): # Maximum 2 robots
                if idx == 0: # Top right
                    cx = x * CELL_SIZE + 3 * CELL_SIZE // 4
                    cy = y * CELL_SIZE + CELL_SIZE // 4 + SCORES_HEIGHT
                else: # Bottom right
                    cx = x * CELL_SIZE + 3 * CELL_SIZE // 4
                    cy = y * CELL_SIZE + 3 * CELL_SIZE // 4 + SCORES_HEIGHT
                color = DARK_BLUE if r.carrying else BLUE
                pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 5)
                font = pygame.font.SysFont(None, 14)
                txt = font.render(str(r.id), True, BLACK)
                screen.blit(txt, (cx - 6, cy - 6))
