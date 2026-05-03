import pygame
import random
from db import save_score, get_best

pygame.init()

WIDTH = 600
HEIGHT = 400
BLOCK = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()

def game(username):

    x, y = WIDTH//2, HEIGHT//2
    dx, dy = 0, 0

    snake = []
    length = 1

    food = (100,100)
    poison = (200,200)

    power = None
    power_timer = 0

    score = 0
    level = 1
    speed = 10

    best = get_best(username)

    obstacles = []

    running = True
    game_over = False

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        if game_over:
            save_score(username, score, level)
            pygame.time.delay(2000)
            return

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]: dx, dy = -BLOCK, 0
        if keys[pygame.K_RIGHT]: dx, dy = BLOCK, 0
        if keys[pygame.K_UP]: dx, dy = 0, -BLOCK
        if keys[pygame.K_DOWN]: dx, dy = 0, BLOCK

        x += dx
        y += dy

        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            game_over = True

        snake.append((x,y))
        if len(snake) > length:
            snake.pop(0)

        if (x,y) in snake[:-1]:
            game_over = True

        # FOOD
        if (x,y) == food:
            score += 1
            length += 1
            food = (random.randrange(0, WIDTH, BLOCK),
                    random.randrange(0, HEIGHT, BLOCK))

        # POISON
        if (x,y) == poison:
            length -= 2
            if length <= 1:
                game_over = True
            poison = (random.randrange(0, WIDTH, BLOCK),
                      random.randrange(0, HEIGHT, BLOCK))

        # POWER
        if power == "speed":
            speed = 20
            power_timer -= 1
            if power_timer <= 0:
                power = None
                speed = 10

        # OBSTACLES
        if level >= 3 and not obstacles:
            for i in range(5):
                obstacles.append((random.randrange(0, WIDTH, BLOCK),
                                  random.randrange(0, HEIGHT, BLOCK)))

        if (x,y) in obstacles:
            game_over = True

        # LEVEL UP
        if score % 5 == 0 and score != 0:
            level += 1

        screen.fill((0,0,0))

        pygame.draw.rect(screen, (255,0,0), (*food, BLOCK, BLOCK))
        pygame.draw.rect(screen, (150,0,0), (*poison, BLOCK, BLOCK))

        for o in obstacles:
            pygame.draw.rect(screen, (100,100,100), (*o, BLOCK, BLOCK))

        for part in snake:
            pygame.draw.rect(screen, (0,255,0), (*part, BLOCK, BLOCK))

        screen.blit(font.render(f"Score:{score}", True, (255,255,255)), (10,10))
        screen.blit(font.render(f"Best:{best}", True, (255,255,255)), (10,30))

        pygame.display.update()
        clock.tick(speed)