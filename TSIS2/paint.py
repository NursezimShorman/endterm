import pygame
import sys
import datetime

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
last_pos = None
preview_surface = None

typing = False
text = ""
text_pos = (0, 0)

font = pygame.font.SysFont("Arial", 20)

screen.fill(WHITE)

# -------------------- FLOOD FILL --------------------
def flood_fill(surface, x, y, new_color):
    target_color = surface.get_at((x, y))
    if target_color == new_color:
        return

    stack = [(x, y)]

    while stack:
        x, y = stack.pop()

        if surface.get_at((x, y)) == target_color:
            surface.set_at((x, y), new_color)

            if x > 0: stack.append((x - 1, y))
            if x < WIDTH - 1: stack.append((x + 1, y))
            if y > 0: stack.append((x, y - 1))
            if y < HEIGHT - 1: stack.append((x, y + 1))

# -------------------- UI --------------------
def draw_ui():
    for i, color in enumerate(colors):
        pygame.draw.rect(screen, color, (10 + i * 40, 10, 30, 30))

    txt = font.render(f"Mode: {mode} | Size: {brush_size}", True, BLACK)
    screen.blit(txt, (10, 50))

    help1 = "B-Brush P-Pencil L-Line R-Rect C-Circle S-Square"
    help2 = "Y-RTriangle Q-ETriangle H-Rhombus F-Fill T-Text"
    help3 = "1/2/3 Size | Cmd/Ctrl+S Save | X Clear"

    screen.blit(font.render(help1, True, BLACK), (10, 80))
    screen.blit(font.render(help2, True, BLACK), (10, 100))
    screen.blit(font.render(help3, True, BLACK), (10, 120))

# -------------------- MAIN LOOP --------------------
running = True

while running:
    draw_ui()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # -------------------- MOUSE DOWN --------------------
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

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

        # -------------------- MOUSE UP --------------------
        if event.type == pygame.MOUSEBUTTONUP:
            end_pos = event.pos
            x1, y1 = start_pos
            x2, y2 = end_pos

            if mode == "line":
                pygame.draw.line(screen, current_color, start_pos, end_pos, brush_size)

            elif mode == "rect":
                rect = pygame.Rect(min(x1, x2), min(y1, y2),
                                   abs(x2 - x1), abs(y2 - y1))
                pygame.draw.rect(screen, current_color, rect, brush_size)

            elif mode == "circle":
                radius = int(((x2 - x1)**2 + (y2 - y1)**2) ** 0.5)
                pygame.draw.circle(screen, current_color, start_pos, radius, brush_size)

            elif mode == "square":
                side = min(abs(x2 - x1), abs(y2 - y1))
                pygame.draw.rect(screen, current_color,
                                 pygame.Rect(x1, y1, side, side), brush_size)

            elif mode == "right_triangle":
                pygame.draw.polygon(screen, current_color,
                                    [(x1, y1), (x1, y2), (x2, y2)], brush_size)

            elif mode == "eq_triangle":
                mid = (x1 + x2) // 2
                pygame.draw.polygon(screen, current_color,
                                    [(mid, y1), (x1, y2), (x2, y2)], brush_size)

            elif mode == "rhombus":
                midx = (x1 + x2) // 2
                midy = (y1 + y2) // 2
                pygame.draw.polygon(screen, current_color,
                                    [(midx, y1), (x2, midy),
                                     (midx, y2), (x1, midy)], brush_size)

            drawing = False

        # -------------------- MOUSE MOVE --------------------
        if event.type == pygame.MOUSEMOTION and drawing:

            if mode in ["brush", "pencil"]:
                pygame.draw.line(screen, current_color, last_pos, event.pos, brush_size)
                last_pos = event.pos

            elif mode == "eraser":
                pygame.draw.line(screen, WHITE, last_pos, event.pos, 20)
                last_pos = event.pos

            elif mode == "line":
                screen.blit(preview_surface, (0, 0))
                pygame.draw.line(screen, current_color, start_pos, event.pos, brush_size)

        # -------------------- KEYBOARD --------------------
        if event.type == pygame.KEYDOWN:

            # MODES
            if event.key == pygame.K_b: mode = "brush"
            elif event.key == pygame.K_p: mode = "pencil"
            elif event.key == pygame.K_l: mode = "line"
            elif event.key == pygame.K_r: mode = "rect"
            elif event.key == pygame.K_c: mode = "circle"
            elif event.key == pygame.K_s: mode = "square"
            elif event.key == pygame.K_y: mode = "right_triangle"
            elif event.key == pygame.K_q: mode = "eq_triangle"
            elif event.key == pygame.K_h: mode = "rhombus"
            elif event.key == pygame.K_f: mode = "fill"
            elif event.key == pygame.K_e: mode = "eraser"
            elif event.key == pygame.K_t: mode = "text"

            # SIZE
            elif event.key == pygame.K_1: brush_size = 2
            elif event.key == pygame.K_2: brush_size = 5
            elif event.key == pygame.K_3: brush_size = 10

            # CLEAR
            elif event.key == pygame.K_x:
                screen.fill(WHITE)

            # SAVE
            mods = pygame.key.get_mods()
            if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                filename = datetime.datetime.now().strftime("drawing_%Y%m%d_%H%M%S.png")
                pygame.image.save(screen, filename)
                print("Saved:", filename)

            # TEXT INPUT
            if typing:
                if event.key == pygame.K_RETURN:
                    screen.blit(preview_surface, (0, 0))
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

    # TEXT PREVIEW
    if typing:
        screen.blit(preview_surface, (0, 0))
        img = font.render(text, True, current_color)
        screen.blit(img, text_pos)

    pygame.display.update()

pygame.quit()
sys.exit()