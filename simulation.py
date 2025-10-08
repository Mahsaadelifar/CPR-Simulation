import pygame
import random
import sys
from collections import defaultdict

from config import *
from robot import *
from grid import *
from base import *

# Functions here run at every simulation step
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

    def step(self):
        for robot in self.grid.robots:
            for message in robot.kb.received_messages["moving_to"]:
                if robot.team == Team.RED:
                    print(ANSI.YELLOW.value + f"Robot {robot.id} received message: {message.id} {message.content}, proposer: {message.proposer.id}, countdown: {message.countdown}" + ANSI.RESET.value)
            for message in robot.kb.read_messages["moving_to"]:
                if robot.team == Team.RED:
                    print(ANSI.GREEN.value + f"Robot {robot.id} read message: {message.id} {message.content}, proposer: {message.proposer.id}" + ANSI.RESET.value)
            if random.random() < 0.5:
                robot.turn(random.choice(list(Dir)))
            robot.plan(str(self.timestep).zfill(3))
        
        for robot in self.grid.robots:
            robot.read_message()
        print("===============================")

        for robot in self.grid.robots:
            robot.planned_move((str(self.timestep).zfill(3)))
            
        self.timestep += 1
        self.check()