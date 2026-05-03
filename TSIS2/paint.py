import pygame
import sys
import datetime
from tools import flood_fill

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Paint App")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
YELLOW = (255, 255, 0)

colors = [BLACK, RED, GREEN, BLUE, YELLOW]

current_color = BLACK
brush_size = 5
mode = "brush"

drawing = False
start_pos = (0, 0)
last_pos = (0, 0)
preview_surface = None

typing = False
text = ""
text_pos = (0, 0)

font = pygame.font.SysFont("Arial", 20)

screen.fill(WHITE)


def draw_ui():
    for i, color in enumerate(colors):
        pygame.draw.rect(screen, color, (10 + i * 40, 10, 30, 30))

    info = font.render(f"Mode: {mode} | Size: {brush_size}", True, BLACK)
    screen.blit(info, (10, 50))

    help_text = "B/P/L/R/C/F/T | 1/2/3 size | Ctrl+S save | X clear"
    screen.blit(font.render(help_text, True, BLACK), (10, 80))


running = True

while running:
    draw_ui()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ---------------- MOUSE DOWN ----------------
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            # color picker
            for i, color in enumerate(colors):
                rect = pygame.Rect(10 + i * 40, 10, 30, 30)
                if rect.collidepoint(x, y):
                    current_color = color

            drawing = True
            start_pos = event.pos
            last_pos = event.pos
            preview_surface = screen.copy()

            if mode == "fill":
                flood_fill(screen, x, y, current_color)

            if mode == "text":
                typing = True
                text = ""
                text_pos = event.pos
                preview_surface = screen.copy()

        # ---------------- MOUSE UP ----------------
        if event.type == pygame.MOUSEBUTTONUP:
            end_pos = event.pos
            x1, y1 = start_pos
            x2, y2 = end_pos

            if mode == "line":
                pygame.draw.line(screen, current_color, start_pos, end_pos, brush_size)

            elif mode == "rect":
                pygame.draw.rect(screen, current_color,
                                  pygame.Rect(min(x1, x2), min(y1, y2),
                                              abs(x2-x1), abs(y2-y1)), brush_size)

            elif mode == "circle":
                radius = int(((x2-x1)**2 + (y2-y1)**2) ** 0.5)
                pygame.draw.circle(screen, current_color, start_pos, radius, brush_size)

            elif mode == "square":
                side = min(abs(x2-x1), abs(y2-y1))
                pygame.draw.rect(screen, current_color, pygame.Rect(x1, y1, side, side), brush_size)

            elif mode == "triangle":
                pygame.draw.polygon(screen, current_color, [(x1,y2),(x2,y2),(x1,y1)], brush_size)

            drawing = False

        # ---------------- MOUSE MOVE ----------------
        if event.type == pygame.MOUSEMOTION and drawing:

            if mode in ["brush", "pencil"]:
                pygame.draw.line(screen, current_color, last_pos, event.pos, brush_size)
                last_pos = event.pos

            elif mode == "eraser":
                pygame.draw.line(screen, WHITE, last_pos, event.pos, brush_size * 3)
                last_pos = event.pos

            elif mode == "line":
                screen.blit(preview_surface, (0, 0))
                pygame.draw.line(screen, current_color, start_pos, event.pos, brush_size)

        # ---------------- KEYBOARD ----------------
        if event.type == pygame.KEYDOWN:

            # modes
            if event.key == pygame.K_b:
                mode = "brush"
            elif event.key == pygame.K_p:
                mode = "pencil"
            elif event.key == pygame.K_l:
                mode = "line"
            elif event.key == pygame.K_r:
                mode = "rect"
            elif event.key == pygame.K_c:
                mode = "circle"
            elif event.key == pygame.K_f:
                mode = "fill"
            elif event.key == pygame.K_t:
                mode = "text"
            elif event.key == pygame.K_e:
                mode = "eraser"

            # size
            elif event.key == pygame.K_1:
                brush_size = 2
            elif event.key == pygame.K_2:
                brush_size = 5
            elif event.key == pygame.K_3:
                brush_size = 10

            # clear
            elif event.key == pygame.K_x:
                screen.fill(WHITE)

            # save
            mods = pygame.key.get_mods()
            if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                filename = datetime.datetime.now().strftime("drawing_%Y%m%d_%H%M%S.png")
                pygame.image.save(screen, filename)
                print("Saved:", filename)

            # text typing
            if typing:
                if event.key == pygame.K_RETURN:
                    img = font.render(text, True, current_color)
                    screen.blit(img, text_pos)
                    typing = False

                elif event.key == pygame.K_ESCAPE:
                    screen.blit(preview_surface, (0, 0))
                    typing = False

                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]

                else:
                    text += event.unicode

    # live text preview
    if typing:
        screen.blit(preview_surface, (0, 0))
        img = font.render(text, True, current_color)
        screen.blit(img, text_pos)

    pygame.display.update()

pygame.quit()
sys.exit()
