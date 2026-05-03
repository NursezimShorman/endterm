import pygame
from ui import main_menu
from racer import game

pygame.init()

while True:
    action = main_menu()

    if action == "play":
        game()

    elif action == "quit":
        pygame.quit()
        break