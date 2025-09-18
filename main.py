import pygame
import sys
from config import X_WINDOW_SIZE, Y_WINDOW_SIZE, FPS
from simulation import Simulation

def main():
    pygame.init()
    screen = pygame.display.set_mode((X_WINDOW_SIZE, Y_WINDOW_SIZE))
    # clock = pygame.time.Clock()
    sim = Simulation()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                sim.step()
        sim.draw(screen)
        pygame.display.flip()
        # clock.tick(FPS)

if __name__=="__main__":
    main()
