import pygame

def main_menu():
    screen = pygame.display.set_mode((400, 600))
    font = pygame.font.SysFont("Verdana", 30)

    while True:
        screen.fill((255,255,255))

        text = font.render("1 Play", True, (0,0,0))
        screen.blit(text, (100,200))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "play"
                if event.key == pygame.K_q:
                    return "quit"