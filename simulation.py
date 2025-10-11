import pygame
import random
import sys
from collections import defaultdict

from config import *
from robot import *
from base import *

class Simulation:
    def __init__(self):
        self.grid = Grid()
        self.timestep = 0

        self.initialize_robots_test()

    def initialize_robots(self):
        # Red team
        red_deposit_pos = [0,0]
        rx,ry = [1,0]
        # Blue team
        blue_deposit_pos = [GRID_SIZE-1, GRID_SIZE-1]
        bx,by = [GRID_SIZE-2,GRID_SIZE-1]
        for i in range(ROBOTS_PER_TEAM):
            r_robot = Robot(grid=self.grid, team=Team.RED, position=[rx,ry], direction = Dir.SOUTH, deposit = red_deposit_pos, timestep=self.timestep)
            b_robot = Robot(grid=self.grid, team=Team.BLUE, position=[bx,by], direction=Dir.NORTH, deposit = blue_deposit_pos, timestep=self.timestep)

            self.grid.add_robot(robot=r_robot, pos=(rx,ry))
            self.grid.add_robot(robot=b_robot, pos=(bx,by))

            rx += 1
            bx -= 1
    
    def initialize_robots_test(self):
        red_deposit_pos = [0,0]
        robot_1 = Robot(grid=self.grid, team=Team.RED, position=[1,0], direction = Dir.SOUTH, deposit = red_deposit_pos, timestep=self.timestep)
        robot_2 = Robot(grid=self.grid, team=Team.RED, position=[1,1], direction = Dir.SOUTH, deposit = red_deposit_pos, timestep=self.timestep)
        robot_3 = Robot(grid=self.grid, team=Team.RED, position=[1,2], direction = Dir.SOUTH, deposit = red_deposit_pos, timestep=self.timestep)
        robot_4 = Robot(grid=self.grid, team=Team.RED, position=[1,3], direction = Dir.SOUTH, deposit = red_deposit_pos, timestep=self.timestep)

        self.grid.add_robot(robot=robot_1, pos=(1,0))
        self.grid.add_robot(robot=robot_2, pos=(1,1))
        self.grid.add_robot(robot=robot_3, pos=(1,2))
        self.grid.add_robot(robot=robot_4, pos=(1,3))

    def draw_grid(self, screen):
        # Draw scores
        pygame.draw.rect(screen, WHITE, (0, 0, X_WINDOW_SIZE, SCORES_HEIGHT))
        font = pygame.font.SysFont(None,24)
        scores = font.render(f"Scores - Red: {self.grid.scores[Team.RED]}   Blue: {self.grid.scores[Team.BLUE]}",True,BLACK)
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
        
    def print_team_messages(self):
        for robot in self.grid.robots:
            print(ANSI.MAGENTA.value + f"Robot {robot.id} messages received:" + ANSI.RESET.value)
            for mtype, messages in robot.kb.received_messages.items():
                for message in messages:
                    print(ANSI.MAGENTA.value + f"  timestep: {message.timestep}, type: {message.mtype}, content: {message.content}, proposer: {message.proposer.id}, countdown: {message.countdown}" + ANSI.RESET.value)
        print("==============================")
        for robot in self.grid.robots:
            print(ANSI.MAGENTA.value + f"Robot {robot.id} messages read:" + ANSI.RESET.value)
            for mtype, messages in robot.kb.read_messages.items():
                for message in messages:
                    print(ANSI.MAGENTA.value + f"  timestep: {message.timestep}, type: {message.mtype}, content: {message.content}, proposer: {message.proposer.id}, countdown: {message.countdown}" + ANSI.RESET.value)
        print("==============================")

    def print_partner_messages(self):
        for robot in self.grid.robots:
            print(ANSI.CYAN.value + f"Robot {robot.id} partner messages received:" + ANSI.RESET.value)
            for pmtype, messages in robot.kb.received_partner_messages.items():
                for message in messages:
                    print(ANSI.CYAN.value + f"  timestep: {message.timestep}, type: {message.mtype}, content: {message.content}, proposer: {message.proposer.id}, countdown: {message.countdown}" + ANSI.RESET.value)
        print("==============================")
        for robot in self.grid.robots:
            print(ANSI.CYAN.value + f"Robot {robot.id} partner messages read:" + ANSI.RESET.value)
            for pmtype, messages in robot.kb.read_partner_messages.items():
                for message in messages:
                    print(ANSI.CYAN.value + f"  timestep: {message.timestep}, type: {message.mtype}, content: {message.content}, proposer: {message.proposer.id}, countdown: {message.countdown}" + ANSI.RESET.value)
        print("==============================")

    def step(self):
        print("========= START OF TIMESTEP " + str(self.timestep) + " =========")
        for robot in self.grid.robots:
            robot.timestep = self.timestep

        for robot in self.grid.robots:
            robot.sense()

        print("PLANNING PHASE")
        for robot in self.grid.robots:
            robot.plan()
        print("END OF PLANNING PHASE")

        print("READING PHASE")
        for robot in self.grid.robots:
            robot.read_message()
        
        self.print_team_messages()
        self.print_partner_messages()
        print("END OF READING PHASE")
    
        print("EXECUTION PHASE")
        for robot in self.grid.robots:
            robot.execute()
        print("END OF EXECUTION PHASE")

        print("========= END OF TIMESTEP " + str(self.timestep) + " =========")
        self.timestep += 1