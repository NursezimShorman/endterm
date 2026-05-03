import pygame
from game import game
from db import get_top10

pygame.init()

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont("Arial", 30)

def input_name():
    name = ""

    while True:
        screen.fill((0,0,0))

        text = font.render("Enter name:", True, (255,255,255))
        name_text = font.render(name, True, (0,255,0))

        screen.blit(text, (200,150))
        screen.blit(name_text, (200,200))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return name
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    name += event.unicode


def leaderboard():
    data = get_top10()

    while True:
        screen.fill((0,0,0))

        y = 50
        for i, row in enumerate(data):
            txt = font.render(f"{i+1}. {row[0]} {row[1]}", True, (255,255,255))
            screen.blit(txt, (100, y))
            y += 30

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return


def menu():
    while True:
        screen.fill((0,0,0))

        screen.blit(font.render("1 PLAY", True, (255,255,255)), (200,120))
        screen.blit(font.render("2 LEADERBOARD", True, (255,255,255)), (200,170))
        screen.blit(font.render("Q QUIT", True, (255,255,255)), (200,220))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "play"
                if event.key == pygame.K_2:
                    return "lb"
                if event.key == pygame.K_q:
                    return "quit"


while True:
    action = menu()

    if action == "play":
        name = input_name()
        game(name)

    elif action == "lb":
        leaderboard()

    elif action == "quit":
        pygame.quit()
        break