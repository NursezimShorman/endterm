import pygame
import random
from persistence import save_score

pygame.init()

# -------------------- WINDOW --------------------
WIDTH = 400
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racer Game")

# -------------------- COLORS --------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)

# -------------------- FPS --------------------
clock = pygame.time.Clock()

# -------------------- FONTS --------------------
font = pygame.font.SysFont("Verdana", 20)
big_font = pygame.font.SysFont("Verdana", 30)

# -------------------- IMAGES --------------------
player_img = pygame.image.load("TSIS3/assets/player.png")
enemy_img = pygame.image.load("TSIS3/assets/enemy.png")

player_img = pygame.transform.scale(player_img, (60, 100))
enemy_img = pygame.transform.scale(enemy_img, (60, 100))


def game():

    player_x = 180
    player_y = 500
    player_speed = 5

    enemy_speed = 5

    coins = 0
    distance = 0

    # -------- TRAFFIC --------
    traffic = []
    for i in range(3):
        traffic.append([random.randint(50, 300), random.randint(-600, 0)])

    # -------- POWER UPS --------
    power = None
    power_time = 0

    power_x = random.randint(50, 300)
    power_y = -200
    power_type = random.choice(["nitro", "shield", "repair"])

    running = True
    game_over = False

    while running:
        screen.fill(WHITE)

        # -------- EVENTS --------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # -------- GAME OVER --------
        if game_over:
            text = big_font.render("GAME OVER", True, BLACK)
            screen.blit(text, (100, 250))

            score = coins + distance
            save_score("Player", score)

            pygame.display.update()
            pygame.time.delay(2000)
            return

        # -------- CONTROL --------
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed

        if player_x < 0:
            player_x = 0
        if player_x > 340:
            player_x = 340

        # -------- DISTANCE --------
        distance += 1

        player_rect = player_img.get_rect(topleft=(player_x, player_y))

        # -------- TRAFFIC --------
        for car in traffic:
            car[1] += enemy_speed

            if car[1] > HEIGHT:
                car[1] = random.randint(-600, -100)
                car[0] = random.randint(50, 300)

            rect = enemy_img.get_rect(topleft=(car[0], car[1]))

            if player_rect.colliderect(rect):
                if power == "shield":
                    power = None
                else:
                    game_over = True

            screen.blit(enemy_img, car)

        # -------- POWER UP --------
        power_y += enemy_speed
        power_rect = pygame.Rect(power_x, power_y, 40, 40)

        pygame.draw.rect(screen, CYAN, power_rect)

        if player_rect.colliderect(power_rect):
            power = power_type

            if power == "nitro":
                power_time = 300
            elif power == "shield":
                power_time = 500
            elif power == "repair":
                game_over = False

            power_y = -200
            power_x = random.randint(50, 300)
            power_type = random.choice(["nitro", "shield", "repair"])

        # -------- POWER LOGIC --------
        if power == "nitro":
            player_speed = 8
            power_time -= 1
            if power_time <= 0:
                power = None
                player_speed = 5

        elif power == "shield":
            power_time -= 1
            if power_time <= 0:
                power = None

        # -------- DIFFICULTY --------
        if distance % 500 == 0:
            enemy_speed += 1

        # -------- DRAW --------
        screen.blit(player_img, (player_x, player_y))

        score_text = font.render(f"Coins: {coins}", True, BLACK)
        dist_text = font.render(f"Distance: {distance}", True, BLACK)

        screen.blit(score_text, (10, 10))
        screen.blit(dist_text, (10, 40))

        if power:
            power_text = font.render(f"Power: {power}", True, BLACK)
            screen.blit(power_text, (10, 70))

        pygame.display.update()
        clock.tick(60)


# -------------------- RUN --------------------
if __name__ == "__main__":
    game()