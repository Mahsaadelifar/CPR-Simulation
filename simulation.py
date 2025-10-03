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
        self.scores = {Team.RED: 0, Team.BLUE: 0}

        self.initialize_robots()

    def initialize_robots(self):
        # Red team
        red_deposit_pos = [0,0]
        rx,ry = [1,0]
        # Blue team
        blue_deposit_pos = [GRID_SIZE-1, GRID_SIZE-1]
        bx,by = [GRID_SIZE-2,GRID_SIZE-1]
        for i in range(ROBOTS_PER_TEAM):
            r_robot = Robot(team=Team.RED, position=[rx,ry], direction = Dir.SOUTH, deposit = red_deposit_pos)
            b_robot = Robot(team=Team.BLUE, position=[bx,by], direction=Dir.NORTH, deposit = blue_deposit_pos)
            self.robots.append(r_robot)
            self.robots.append(b_robot)
            rx += 1
            bx -= 1

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
            robots_by_cell[tuple(r.pos)][r.team].append(r)

        for (x,y), teams in robots_by_cell.items():
            # Red team
            for idx, r in enumerate(teams[Team.RED][:2]): # Maximum 2 robots
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
            for idx, r in enumerate(teams[Team.BLUE][:2]): # Maximum 2 robots
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