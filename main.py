import pygame
import sys
from config import X_WINDOW_SIZE, Y_WINDOW_SIZE
from simulation import Simulation
from robot import *

def main():
    pygame.init()
    screen = pygame.display.set_mode((X_WINDOW_SIZE, Y_WINDOW_SIZE))
    sim = Simulation()
    for message in sim.grid.robots[0].kb.received_messages["moving_to"]:
        print(message.id, message.content, message.countdown)
    while True:  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                sim.step()  # currently, tells all robots to attempt reading messages and print out their knowledge base

            # TEST SENDING/RECEIVING/READING MESSAGES
            if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                m = Message(id="000", content=(1,1), proposer=None, acceptor=None)
                sim.grid.robots[0].send_to_all(m)
                for robot in sim.grid.robots:
                    robot.read_message()
                    for message in robot.kb.received_messages["moving_to"]:
                        print(f"{robot.id} received message: '{message.id}, {message.content}, {message.countdown}'")
                    for message in robot.kb.read_messages["moving_to"]:
                        print(f"{robot.id} read message: '{message.id}, {message.content}, {message.countdown}'")
        sim.draw(screen)
        pygame.display.flip()

if __name__=="__main__":
    main()
