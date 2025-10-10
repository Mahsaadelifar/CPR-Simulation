import pygame
import random
import sys
from collections import defaultdict

from config import *
from robot import *
from grid import *
from base import *

class Simulation:
    def __init__(self):
        self.grid = Grid()
        self.scores = {Team.RED: 0, Team.BLUE: 0}
        self.timestep = 0

        self.initialize_robots()

    def initialize_robots(self):
        # Red team
        red_deposit_pos = [0,0]
        rx,ry = [1,0]
        # Blue team
        blue_deposit_pos = [GRID_SIZE-1, GRID_SIZE-1]
        bx,by = [GRID_SIZE-2,GRID_SIZE-1]
        for i in range(ROBOTS_PER_TEAM):
            r_robot = Robot(grid=self.grid, team=Team.RED, position=[rx,ry], direction = Dir.SOUTH, deposit = red_deposit_pos)
            b_robot = Robot(grid=self.grid, team=Team.BLUE, position=[bx,by], direction=Dir.NORTH, deposit = blue_deposit_pos)

            self.grid.add_robot(robot=r_robot, pos=(rx,ry))
            self.grid.add_robot(robot=b_robot, pos=(bx,by))

            rx += 1
            bx -= 1

    def draw_grid(self, screen):
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
                font = pygame.font.SysFont(None, 14)
                txt = font.render(str(tile.gold), True, BLACK)
                cx = gx * CELL_SIZE + CELL_SIZE // 2
                cy = gy * CELL_SIZE + CELL_SIZE // 2 + SCORES_HEIGHT
                pygame.draw.circle(screen, YELLOW, (cx, cy), CELL_SIZE // 6)
                screen.blit(txt, txt.get_rect(center = (cx, cy)))

    def check(self):
        for (gx, gy), tile in self.grid.tiles.items():
            teams = {Team.RED: [], Team.BLUE: []}
            for r in tile.robots:
                teams[r.team].append(r)

            # This shouldn't be checked inside simulation, simulation should allow however many robots. The robot's internal logic is the one that should be checking for this
            if len(teams[Team.RED]) > 2 or len(teams[Team.BLUE]) >2:
                print(ANSI.RED.value + f"Error: More than 2 robots of the same team on tile {(gx,gy)}" + ANSI.RESET.value)
                print("Robots on tile:")
                for robot in tile.robots:
                    print(f"Robot ID: {robot.id}")



    def draw_robots(self, screen):
        for (gx, gy), tile in self.grid.tiles.items():
            teams = {Team.RED: [], Team.BLUE: []}
            for r in tile.robots:
                teams[r.team].append(r)

            # Red team
            for idx, r in enumerate(teams[Team.RED][:2]): # Maximum 2 robots
                if idx == 0: # Top left
                    cx = gx * CELL_SIZE + CELL_SIZE // 4
                    cy = gy * CELL_SIZE + CELL_SIZE // 4 + SCORES_HEIGHT
                else: # Bottom left
                    cx = gx * CELL_SIZE + CELL_SIZE // 4
                    cy = gy * CELL_SIZE + 3 * CELL_SIZE // 4 + SCORES_HEIGHT
                color = DARK_RED if r.carrying else RED
                pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 5)
                font = pygame.font.SysFont(None, 14)
                txt = font.render(str(r.id), True, BLACK)
                screen.blit(txt, txt.get_rect(center = (cx, cy)))
                self.draw_directions(screen, cx, cy, r.dir)

            # Blue team
            for idx, r in enumerate(teams[Team.BLUE][:2]): # Maximum 2 robots
                if idx == 0: # Top right
                    cx = gx * CELL_SIZE + 3 * CELL_SIZE // 4
                    cy = gy * CELL_SIZE + CELL_SIZE // 4 + SCORES_HEIGHT
                else: # Bottom right
                    cx = gx * CELL_SIZE + 3 * CELL_SIZE // 4
                    cy = gy * CELL_SIZE + 3 * CELL_SIZE // 4 + SCORES_HEIGHT
                color = DARK_BLUE if r.carrying else BLUE
                pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 5)
                font = pygame.font.SysFont(None, 14)
                txt = font.render(str(r.id), True, BLACK)
                screen.blit(txt, txt.get_rect(center = (cx, cy)))
                self.draw_directions(screen, cx, cy, r.dir)

    def draw_directions(self, screen, cx, cy, direction):
        if direction == Dir.NORTH:
            pygame.draw.circle(screen, BLACK, (cx, cy - CELL_SIZE // 5), CELL_SIZE // 20)
        elif direction == Dir.EAST:
            pygame.draw.circle(screen, BLACK, (cx + CELL_SIZE // 5, cy), CELL_SIZE // 20)
        elif direction == Dir.SOUTH:
            pygame.draw.circle(screen, BLACK, (cx, cy + CELL_SIZE // 5), CELL_SIZE // 20)
        elif direction == Dir.WEST:
            pygame.draw.circle(screen, BLACK, (cx - CELL_SIZE // 5, cy), CELL_SIZE // 20)

    def draw(self, screen):
        screen.fill(WHITE)

        self.draw_grid(screen)
        self.draw_robots(screen)

    #-------------------- UPDATING GRID & ROBOTS AT EACH TIMESTEP ---------------------------------------------------

    def do_pickup(self, robotA, robotB, tile):
        robotA.carrying, robotB.carrying = True
        robotA.partner_id, robotB.partner_id = robotB.id, robotA.id
        robotA.partner, robotB.partner = robotB, robotA
        tile.gold -= 1
        #IDK HOW TO ADD SCORE TO TEAM BUT I NEED TO ADD IT HERE

    def do_failed_carry(self, robotA, robotB, tile):
        robotA.carrying, robotB.carrying = False
        robotA.partner_id, robotB.partner_id = None
        robotA.partner, robotB.partner = None
        tile.gold += 1

        
    def step(self):
        timestep = str(self.timestep).zfill(3)

        #iterate by robot to plan and execute
        for robot in self.grid.robots:
            tile_robot_actions = {}
            tile_actions_occur = []

            robot.plan(timestep)
            robot.read_message()
            robot.read_message() #NOT SURE IF MY CHANGES MADE IT STILL CORRECT
            robot.clean_messages(timestep)
            action = robot.execute(timestep)
            #IMPORTANT: not including turns and moves because that's handled by 
            # the execute function inside Robot class already
            tile_robot_actions[robot] = action
            tile_actions_occur.append(robot.pos)
        
        #iterate by tile to carry out actions at each tile
        for [x,y] in tile_actions_occur:
            current_tile = self.grid.tiles[(x,y)]
            current_tile_robots = current_tile.robots
            current_tile_redteam = [robot for robot in current_tile_robots if robot.team == Team.RED]
            current_tile_blueteam = [robot for robot in current_tile_robots if robot.team == Team.BLUE]
            current_tile_gold = current_tile.gold

            
            #processing deposits -----------------------------------------------------------------------
            if current_tile.deposit: #check that current tile IS a deposit
                deposits = [robot for robot, action in tile_robot_actions.items() if action == "deposit"]
                for robot in deposits:
                    robot.partner_id = None
                    robot.partner = None
                    #add score to team idk how

                #remove processed robots from dict
                for robot in deposits:
                    del tile_robot_actions[robot]

            #processing pickups -----------------------------------------------------------------------
            pickups = [robot for robot, action in tile_robot_actions.items() if action == "pickup_gold"]
            print(f"all pickups: {pickups}]")
            redteam_pickups = [robot for robot in pickups if robot in current_tile_redteam]
            blueteam_pickups = [robot for robot in pickups if robot in current_tile_blueteam]
            print(f"redteam pickps: {redteam_pickups}")
            print(f"blueteam pickps: {redteam_pickups}")
            
            red_pickup_valid = (len(set(redteam_pickups)) == 2)
            blue_pickup_valid = (len(set(blueteam_pickups)) == 2)

            #both teams valid and are able to pick up at the same time
            if red_pickup_valid and blue_pickup_valid and current_tile.gold > 1:
                self.do_pickup(redteam_pickups[0],redteam_pickups[1],current_tile)
                self.do_pickup(blueteam_pickups[0],blueteam_pickups[1],current_tile)
            #both teams are valid but there is not enough gold to pick up at the same time
            elif red_pickup_valid and blue_pickup_valid and current_tile.gold <= 1:
                print(f"PICKUP FAILURE: both teams failed pickup at {(x,y)}, not enough gold present")

            #only red team valid and enough gold
            elif red_pickup_valid and (not blue_pickup_valid) and current_tile.gold > 0:
                print(f"PICKUP SUCCESS: red team successful pickup at {(x,y)} by robots {[robot.id for robot in redteam_pickups]}")
                print(f"PICKUP FAILURE: blue team failed pickup at {(x,y)} by robots {[robot.id for robot in blueteam_pickups]}")
                self.do_pickup(redteam_pickups[0],redteam_pickups[1],current_tile)
            #only red team valid and not enough gold
            elif red_pickup_valid and (not blue_pickup_valid) and current_tile.gold <= 0:
                print(f"PICKUP FAILURE: red team failed pickup at {(x,y)} by robots {[robot.id for robot in redteam_pickups]},not enough gold present")
                print(f"PICKUP FAILURE: blue team failed pickup at {(x,y)} by robots {[robot.id for robot in blueteam_pickups]}")

            #only blue team valid and enough gold
            elif blue_pickup_valid and (not red_pickup_valid) and current_tile.gold > 0:
                print(f"PICKUP SUCCESS: blue team successful pickup at {(x,y)} by robots {[robot.id for robot in blueteam_pickups]}")
                print(f"PICKUP FAILURE: red team failed pickup at {(x,y)} by robots {[robot.id for robot in redteam_pickups]}")
                self.do_pickup(blueteam_pickups[0],blueteam_pickups[1],current_tile)
            #only blue team valid and not enough gold
            elif blue_pickup_valid and (not red_pickup_valid) and current_tile.gold <= 0:
                print(f"PICKUP FAILURE: blue team successful pickup at {(x,y)} by robots {[robot.id for robot in blueteam_pickups]}, not enough gold present")
                print(f"PICKUP FAILURE: red team failed pickup at {(x,y)} by robots {[robot.id for robot in redteam_pickups]}")

            #neither teams valid
            else:
                #print(f"PICKUP FAILURE: both red and blue teams attempted pickup at {(x,y)}")
                pass
            
            #remove processed robots from dict
            for robot in pickups:
                del tile_robot_actions[robot]
            
            #processing gold drops -----------------------------------------------------------------------

            #Check this line!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Please !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            red_team_partnered = [robot for robot in current_tile_redteam if (robot.partner_id is not None and robot.carrying == True)]
            blue_team_partnered = [robot for robot in current_tile_blueteam if (robot.partner_id is not None and robot.carrying == True)]

            red_partners = []
            for robot1 in red_team_partnered:
                for robot2 in red_team_partnered:
                    if robot2.id != robot1.id and robot1.partner_id == robot2.id:
                        if [robot1, robot2] not in red_partners:
                            red_partners.append([robot1,robot2])

            blue_partners = []
            for robot1 in blue_team_partnered:
                for robot2 in blue_team_partnered:
                    if robot2.id != robot1.id and robot1.partner_id == robot2.id:
                        if [robot1, robot2] not in blue_partners:
                            blue_partners.append([robot1,robot2])
            
            for [RobotA, RobotB] in red_partners:
                #to drop, they must be facing different directions and moving. Turning doesn't matter
                if (tile_robot_actions[RobotA] == tile_robot_actions[RobotB]) and (RobotA.dir != RobotB.dir):
                    self.do_failed_carry(RobotA,RobotB,current_tile)

            for [RobotA, RobotB] in blue_partners:
                #to drop, they must be facing different directions and moving. Turning doesn't matter
                if (tile_robot_actions[RobotA] == tile_robot_actions[RobotB]) and (RobotA.dir != RobotB.dir):
                    self.do_failed_carry(RobotA,RobotB,current_tile)

        
        print("Timestep:" + str(self.timestep).zfill(3))
        self.check_messages()
        self.timestep += 1

    #maybe just make a print messages method in robot class and use it here I think this is a little odd
    def check_messages(self):
        for robot in self.grid.robots:
            for message in robot.kb.received_messages["moving_to"]:
                if robot.team == Team.RED:
                    print(ANSI.YELLOW.value + f"Robot {robot.id} received message: {message.id} {message.content}, proposer: {message.proposer.id}, countdown: {message.countdown}" + ANSI.RESET.value)
            for message in robot.kb.read_messages["moving_to"]:
                if robot.team == Team.RED:
                    print(ANSI.GREEN.value + f"Robot {robot.id} read message: {message.id} {message.content}, proposer: {message.proposer.id}" + ANSI.RESET.value)
        print("=================")