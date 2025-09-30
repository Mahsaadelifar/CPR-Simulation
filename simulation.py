import pygame
import random
import sys
from collections import defaultdict

from config import *
from robot import Robot
from grid import Grid
from base import *

# Functions here run at every simulation step
class Simulation:
    def __init__(self):
        self.grid = Grid()
        self.robots = []
        for i in range(ROBOTS_PER_TEAM):
            # Red team
            
            red_deposit_pos = Position(0, 0)
            rx = random.randint(0, 3)
            ry = random.randint(0, 3)
            red_robot = Robot(Position(rx, ry), Team.RED, red_deposit_pos)
            self.robots.append(red_robot)
            self.grid.tiles[(rx,ry)].robots.append(red_robot)
            


            # Blue team
            blue_deposit_pos = Position(GRID_SIZE - 1, GRID_SIZE - 1)
            bx = random.randint(GRID_SIZE - 4, GRID_SIZE - 1)
            by = random.randint(GRID_SIZE - 4, GRID_SIZE - 1)
            blue_robot = Robot(Position(bx, by), Team.BLUE, blue_deposit_pos)
            self.robots.append(blue_robot)
            self.grid.tiles[(bx,by)].robots.append(blue_robot)


        self.grid.update_robots_positions(self.robots)
        self.scores = {Team.RED: 0, Team.BLUE: 0}
        #self.messages = [] why does the simulation have a self.messages??
    

    def handle_pickups(self, decisions):
        pickup_attempts = defaultdict(lambda: defaultdict(list))

        #store positions where at least one robot is trying to pick up gold
        pickup_positions = set((r.position.x,r.position.y) for r in self.robots if decisions[r.id] == 'pickup')

        for (x,y) in pickup_positions:
            tile_here = self.grid.tiles[(x,y)]
            robots_here = tile_here.robots #list of robots on the tile object
            gold_here = tile_here.gold

            team_groups = defaultdict(list) #key is the team, value is the robot object
            for rb in robots_here:
                if decisions[rb.id] == "pickup" and not rb.carrying: #if there are other robots on that square but it's not trying to pick up does the pickup still fail?? cause I don't check for that rn
                    team_groups[rb.team].append(rb) 

                if len(team_groups) ==0:
                    continue #no robots at the position

                team_ids = list(team_groups.keys())
                team1_id = team_ids[0]
                team2_id = team_ids[1] if len(team_ids)>1 else None

                team1 = list(set(team_groups[team1_id])) #get list of robots in team one from the stored info
                team2 = list(set(team_groups[team2_id] if team2_id else [])) #get list of robots in team two from the stored info

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
               gold_here = self.grid.tiles[pos].gold
               for team_id, pair_list in teams.items():
                   for (a,b) in pair_list:
                       if gold_here >=1:
                           gold_here -= 1
                           self.grid.tiles[pos].gold = gold_here
                           print(f"PICKUP SUCCESS: Robots {a.id} & {b.id} from team {team_id.name} picked up gold at {pos}")
                       else:
                           print(f"PICKUP FAILURE: Robots {a.id} & {b.id} from team {team_id.name} failed to pickup gold")

            ### Handle deposits ###
            for r in list(self.robots):
                if r.carrying and r.position == r.deposit:
                    partner = r.partner
                    if partner and partner.carrying and partner.team==r.team and partner.position == r.position:
                        self.scores[r.team] += 1
                        print(f"DEPOSIT SUCCESS: Robots {r.id} & {partner.id} from team {'Red' if r.team==0 else 'Blue'} deposited gold at {r.deposit}")

            self.grid.update_robots_positions(self.robots)


    # Main logic for each simulation step
    def step(self): # Runs at each simulation step
        decisions = {} # Robot_id : action
        sensed_store = {} # Robot_id : sensed dict
        self.messages = [] # Clear messages each turn

        for r in self.robots:
            sensed = r.sense(self.grid) 
            sensed_store[r.id] = sensed
            decisions[r.id] = r.decide_final(sensed_store[r.id], self.grid) 
        
            #for pos,info in sensed.items():
            #    if info['gold']>0:
                    #self.messages.append({'from':r.id,'team':r.team,'type':'gold','pos':pos}) ifnoring this cause it's gonna break the current messaging system
                    #break
            #        pass

        # Turn actions
        for r in self.robots:
            act = decisions[r.id]
            if act == 'turn_left':
                r.facing = (r.facing - 1) % 4
                r.last_action = 'turn_left'
            elif act == 'turn_right':
                r.facing = (r.facing + 1) % 4
                r.last_action = 'turn_right'

        # Storing movements planned by each robot in a move_intents dict
        move_intents = {}
        for r in self.robots:
            if decisions[r.id] == 'move':
                dx,dy = DIR_VECT[r.facing]
                nx,ny = wrap_pos(r.position.x +dx, r.position.y +dy)
                r.planned_move = Position(nx,ny)
                move_intents[r.id] = r.planned_move
            else:
                r.planned_move = None

        """
        # Cooperative check for partners ALREADY MOVED TO INSIDE ROBOT CLASS
        id_to_robot = {r.id:r for r in self.robots}
        for r in self.robots:
            if r.carrying and r.partner_id is not None:
                partner = id_to_robot.get(r.partner_id)
                if partner and partner.planned_move != r.planned_move:
                    r.planned_move = Position(r.position.x, r.position.y)
                    partner.planned_move = Position(partner.position.x, partner.position.y)
                    print(f"WAIT: Robots {r.id} & {partner.id} waiting to align moves")
        """

        # Execute moves
        for r in self.robots:
            if r.planned_move:
                #updating robots present at each tile
                self.grid.tiles[(r.position.x,r.position.y)].robot_off_tile(r)
                self.grid.tiles[(r.planned_move.x,r.planned_move.y)].robot_on_tile(r)

                #updating robot positions
                r.position = r.planned_move
            #r.history.add((r.position.x, r.position.y)) #this needs to be removed. not allowed for decentrlisation
    
        self.handle_pickups(decisions)

    """
        ### Handle pickups ###
        pickup_attempts = defaultdict(lambda: defaultdict(list))

        #store positions where at least one robot is trying to pick up gold
        pickup_positions = set((r.position.x,r.position.y) for r in self.robots if decisions[r.id] == 'pickup')

        #iterate through positions to get robots at each position
        for pos in pickup_positions:
            robots_here = self.grid.robots_at(pos)
            gold_here = self.grid.tiles[pos].gold #number of gold at the position

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

            team1 = list(set(team_groups[team1_id])) #get list of robots in team one from the stored info
            team2 = list(set(team_groups[team2_id] if team2_id else [])) #get list of robots in team two from the stored info

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
           gold_here = self.grid.tiles[pos].gold
           for team_id, pair_list in teams.items():
               for (a,b) in pair_list:
                   if gold_here >=1:
                       #a.carrying = b.carrying = True  moved all this inside robot class to decentralise
                       #a.partner_id, b.partner_id = b.id, a.id
                       #a.partner = b
                       #b.partner = a
                       gold_here -= 1
                       self.grid.tiles[pos].gold = gold_here
                       print(f"PICKUP SUCCESS: Robots {a.id} & {b.id} from team {team_id.name} picked up gold at {pos}")
                   else:
                       print(f"PICKUP FAILURE: Robots {a.id} & {b.id} from team {team_id.name} failed to pickup gold") 
                   

        ### Handle deposits ###
        for r in list(self.robots):
            if r.carrying and r.position == r.deposit:
                partner = r.partner
                if partner and partner.carrying and partner.team==r.team and partner.position == r.position:
                    #r.carrying = partner.carrying = False 
                    #r.partner_id = partner.partner_id = None.      moved all of this logic into robot class to decentralise
                    #r.partner = None
                    self.scores[r.team] += 1
                    print(f"DEPOSIT SUCCESS: Robots {r.id} & {partner.id} from team {'Red' if r.team==0 else 'Blue'} deposited gold at {r.deposit}")

        self.grid.update_robots_positions(self.robots)
    """
    


    # Draw directions onto robot
    def draw_directions(self, screen, cx, cy, facing):
        if facing == 0: # North
            pygame.draw.polygon(screen, BLACK, [(cx, cy - 12), (cx - 7, cy), (cx + 7, cy)])
        elif facing == 1: # East
            pygame.draw.polygon(screen, BLACK, [(cx + 12, cy), (cx, cy - 7), (cx, cy + 7)])
        elif facing == 2: # South
            pygame.draw.polygon(screen, BLACK, [(cx, cy + 12), (cx - 7, cy), (cx + 7, cy)])
        elif facing == 3: # West
            pygame.draw.polygon(screen, BLACK, [(cx - 12, cy), (cx, cy - 7), (cx, cy + 7)])

    # Draw pygame stuff
    def draw(self, screen):
        screen.fill(WHITE)

        # Draw scores
        pygame.draw.rect(screen, WHITE, (0, 0, X_WINDOW_SIZE, SCORES_HEIGHT))
        font = pygame.font.SysFont(None,24)
        scores = font.render(f"Scores - Red: {self.scores[Team.RED]}   Blue: {self.scores[Team.BLUE]}",True,BLACK)
        screen.blit(scores,(8,8))

        # Draw grid
        for (gx, gy), tile in self.grid.tiles.items():
            rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE + SCORES_HEIGHT, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, BLACK, rect, 1)

            # Draw deposit
            if tile.deposit:
                pygame.draw.rect(screen, DEPOSIT_COL, (gx * CELL_SIZE + 2, gy * CELL_SIZE + 2 + SCORES_HEIGHT, CELL_SIZE - 4, CELL_SIZE - 4))

            # Draw gold
            if tile.gold > 0:
                font = pygame.font.SysFont(None, 16)
                txt = font.render(str(tile.gold), True, BLACK)
                cx = gx * CELL_SIZE + CELL_SIZE // 2
                cy = gy * CELL_SIZE + CELL_SIZE // 2 + SCORES_HEIGHT
                pygame.draw.circle(screen, YELLOW, (cx, cy), 8)
                screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))
        
        # Draw robots
        robots_by_cell = defaultdict(lambda: {Team.RED: [], Team.BLUE: []}) # Creates dict of robots from each team for each cell
        for r in self.robots:
            robots_by_cell[r.position.get_tuple()][r.team].append(r)

        for (x,y), teams in robots_by_cell.items():
            # Red team
            for idx, r in enumerate(teams[Team.RED][:2]): # Maximum 2 robots
                if idx == 0: # Top left
                    cx = x * CELL_SIZE + CELL_SIZE // 4
                    cy = y * CELL_SIZE + CELL_SIZE // 4 + SCORES_HEIGHT
                    self.draw_directions(screen, cx, cy, r.facing)
                else: # Bottom left
                    cx = x * CELL_SIZE + CELL_SIZE // 4
                    cy = y * CELL_SIZE + 3 * CELL_SIZE // 4 + SCORES_HEIGHT
                    self.draw_directions(screen, cx, cy, r.facing)
                color = DARK_RED if r.carrying else RED
                pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 5)
                font = pygame.font.SysFont(None, 14)
                txt = font.render(str(r.id), True, BLACK)
                screen.blit(txt, (cx - 6, cy - 6))
            
            # Blue team
            for idx, r in enumerate(teams[Team.BLUE][:2]): # Maximum 2 robots
                if idx == 0: # Top right
                    cx = x * CELL_SIZE + 3 * CELL_SIZE // 4
                    cy = y * CELL_SIZE + CELL_SIZE // 4 + SCORES_HEIGHT
                    self.draw_directions(screen, cx, cy, r.facing)
                else: # Bottom right
                    cx = x * CELL_SIZE + 3 * CELL_SIZE // 4
                    cy = y * CELL_SIZE + 3 * CELL_SIZE // 4 + SCORES_HEIGHT
                    self.draw_directions(screen, cx, cy, r.facing)
                color = DARK_BLUE if r.carrying else BLUE
                pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 5)
                font = pygame.font.SysFont(None, 14)
                txt = font.render(str(r.id), True, BLACK)
                screen.blit(txt, (cx - 6, cy - 6))
