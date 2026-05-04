from pathlib import Path
import random

import pygame

from food import Food, PoisonFood, PowerUp
from game_object import Point
from persistence import (
    SNAKE_COLOR_PRESETS,
    get_personal_best,
    load_leaderboard,
    load_settings,
    prepare_database,
    save_game_result,
    save_settings,
)
from ui import BG, MUTED, WHITE, Button, draw_center_text, draw_left_text, draw_panel
from wall import Wall
from worm import Worm


WIDTH = 400
HEIGHT = 300
TILE = 20
BASE_FPS = 5
FOODS_PER_LEVEL = 3
FOOD_LIFETIME_MS = 5000
POWERUP_FIELD_LIFETIME_MS = 8000
POWERUP_EFFECT_MS = 5000

BASE_DIR = Path(__file__).resolve().parent


def normalize_username(name):
    clean = (name or "").strip()
    if not clean:
        clean = "Player"
    return clean[:16]


def format_played_at(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return "-"


def draw_menu_background(screen):
    create_background(screen, WIDTH, HEIGHT)
    draw_panel(screen, pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 40))


def create_background(screen, width, height):
    colors = [(255, 255, 255), (212, 212, 212)]
    tile_width = TILE
    y = 0
    while y < height:
        x = 0
        while x < width:
            row = y // tile_width
            col = x // tile_width
            pygame.draw.rect(screen, colors[(row + col) % 2], pygame.Rect(x, y, tile_width, tile_width))
            x += tile_width
        y += tile_width


def draw_game_background(screen, show_grid):
    create_background(screen, WIDTH, HEIGHT)

    if not show_grid:
        return

    for x in range(0, WIDTH, TILE):
        pygame.draw.line(screen, (95, 95, 95), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, TILE):
        pygame.draw.line(screen, (95, 95, 95), (0, y), (WIDTH, y), 1)


def draw_game_hud(screen, font_small, font_tiny, score, level, best, username, effect, shield_active, db_ready):
    panel = pygame.Surface((WIDTH, 48), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 110))
    screen.blit(panel, (0, 0))

    draw_left_text(screen, f"{username}   Score: {score}   Level: {level}", font_small, WHITE, 8, 6)
    draw_left_text(screen, f"Best: {best}", font_small, WHITE, 8, 24)

    effect_label = "none"
    if effect == "speed":
        effect_label = "speed boost"
    elif effect == "slow":
        effect_label = "slow motion"
    elif shield_active:
        effect_label = "shield"

    draw_left_text(screen, f"Power-up: {effect_label}", font_tiny, WHITE, 240, 8)


def cycle_color(current_rgb):
    presets = [list(rgb) for rgb in SNAKE_COLOR_PRESETS]
    current = list(current_rgb)

    if current not in presets:
        return presets[0]

    index = presets.index(current)
    return presets[(index + 1) % len(presets)]


def clone_points(points):
    return [Point(point.X, point.Y) for point in points]


def get_point_positions(*objects):
    positions = set()
    for obj in objects:
        if obj and getattr(obj, "points", None):
            point = obj.points[0]
            positions.add((point.X, point.Y))
    return positions


def run_game(screen, clock, settings, username, personal_best, db_ready):
    font_small = pygame.font.SysFont("Verdana", 16)
    font_tiny = pygame.font.SysFont("Verdana", 13)
    pause_font = pygame.font.SysFont("Verdana", 26, bold=True)

    worm = Worm(TILE)
    worm.set_color(settings["snake_color"])

    wall = Wall(TILE)
    wall.refresh_obstacles(worm.get_occupied_positions(), worm.get_head(), WIDTH, HEIGHT)

    food = Food(TILE)
    poison = PoisonFood(TILE)
    powerup = PowerUp(TILE)

    score = 0
    eaten_food = 0
    fps = BASE_FPS
    paused = False

    active_effect = None
    effect_until = 0
    shield_active = False
    next_powerup_spawn_at = pygame.time.get_ticks() + random.randint(7000, 10000)

    blocked = worm.get_occupied_positions() | wall.get_occupied_positions()
    if not food.respawn(blocked, WIDTH, HEIGHT):
        return {
            "status": "game_over",
            "username": username,
            "score": score,
            "level": wall.get_level_number(),
            "personal_best": max(personal_best, score),
        }

    blocked = worm.get_occupied_positions() | wall.get_occupied_positions() | get_point_positions(food)
    poison.respawn(blocked, WIDTH, HEIGHT)

    while True:
        filtered_events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return {"status": "quit"}

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return {"status": "menu"}

            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused
            else:
                filtered_events.append(event)

        now = pygame.time.get_ticks()

        if not paused:
            if active_effect in ("speed", "slow") and now >= effect_until:
                active_effect = None

            before_move = clone_points(worm.points)
            worm.process_input(filtered_events)
            worm.move()

            head = worm.get_head()
            collided = (
                head.X < 0
                or head.Y < 0
                or head.X >= WIDTH
                or head.Y >= HEIGHT
                or wall.is_collision(head)
                or worm.is_self_collision()
            )

            if collided:
                if shield_active:
                    shield_active = False
                    worm.points = before_move
                    head = worm.get_head()
                else:
                    return {
                        "status": "game_over",
                        "username": username,
                        "score": score,
                        "level": wall.get_level_number(),
                        "personal_best": max(personal_best, score),
                    }

            if food.can_eat(head):
                worm.increase()
                score += food.weight
                eaten_food += 1

                blocked = worm.get_occupied_positions() | wall.get_occupied_positions()
                if not food.respawn(blocked, WIDTH, HEIGHT):
                    return {
                        "status": "game_over",
                        "username": username,
                        "score": score,
                        "level": wall.get_level_number(),
                        "personal_best": max(personal_best, score),
                    }

                blocked |= get_point_positions(food, poison)
                poison.respawn(blocked, WIDTH, HEIGHT)

                if eaten_food % FOODS_PER_LEVEL == 0:
                    fps += 1
                    wall.next_level(worm.get_occupied_positions(), worm.get_head(), WIDTH, HEIGHT)

                    blocked = worm.get_occupied_positions() | wall.get_occupied_positions()
                    if not food.respawn(blocked, WIDTH, HEIGHT):
                        return {
                            "status": "game_over",
                            "username": username,
                            "score": score,
                            "level": wall.get_level_number(),
                            "personal_best": max(personal_best, score),
                        }

                    blocked |= get_point_positions(food)
                    poison.respawn(blocked, WIDTH, HEIGHT)

                    powerup.clear()
                    next_powerup_spawn_at = now + random.randint(6000, 9000)

            elif food.is_expired(now, FOOD_LIFETIME_MS):
                blocked = worm.get_occupied_positions() | wall.get_occupied_positions()
                blocked |= get_point_positions(poison)
                if not food.respawn(blocked, WIDTH, HEIGHT):
                    return {
                        "status": "game_over",
                        "username": username,
                        "score": score,
                        "level": wall.get_level_number(),
                        "personal_best": max(personal_best, score),
                    }

            if poison.can_eat(head):
                new_length = worm.decrease(2)
                if new_length <= 1:
                    return {
                        "status": "game_over",
                        "username": username,
                        "score": score,
                        "level": wall.get_level_number(),
                        "personal_best": max(personal_best, score),
                    }

                blocked = worm.get_occupied_positions() | wall.get_occupied_positions()
                blocked |= get_point_positions(food)
                poison.respawn(blocked, WIDTH, HEIGHT)

            if not powerup.is_on_field() and now >= next_powerup_spawn_at:
                blocked = worm.get_occupied_positions() | wall.get_occupied_positions()
                blocked |= get_point_positions(food, poison)
                powerup.spawn(blocked, WIDTH, HEIGHT, now)
                next_powerup_spawn_at = now + random.randint(10000, 14000)

            if powerup.is_expired(now, POWERUP_FIELD_LIFETIME_MS):
                powerup.clear()

            if powerup.can_collect(head):
                kind = powerup.kind
                powerup.clear()

                if kind == "speed":
                    active_effect = "speed"
                    effect_until = now + POWERUP_EFFECT_MS
                elif kind == "slow":
                    active_effect = "slow"
                    effect_until = now + POWERUP_EFFECT_MS
                elif kind == "shield":
                    shield_active = True

                next_powerup_spawn_at = now + random.randint(10000, 14000)

        draw_game_background(screen, settings["grid"])
        food.draw(screen)
        poison.draw(screen)
        wall.draw(screen)
        if powerup.is_on_field():
            powerup.draw(screen)
        worm.draw(screen)

        draw_game_hud(
            screen,
            font_small,
            font_tiny,
            score,
            wall.get_level_number(),
            max(personal_best, score),
            username,
            active_effect,
            shield_active,
            db_ready,
        )

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            draw_center_text(screen, "PAUSED", pause_font, WHITE, HEIGHT // 2)
            draw_center_text(screen, "Press P to continue", font_tiny, WHITE, HEIGHT // 2 + 30)

        pygame.display.flip()

        tick_fps = fps
        if active_effect == "speed":
            tick_fps += 3
        elif active_effect == "slow":
            tick_fps = max(3, tick_fps - 2)

        clock.tick(max(3, tick_fps))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TSIS4 Snake")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("Verdana", 30, bold=True)
    text_font = pygame.font.SysFont("Verdana", 20)
    small_font = pygame.font.SysFont("Verdana", 16)
    tiny_font = pygame.font.SysFont("Verdana", 13)

    settings = load_settings(BASE_DIR)
    db_ready = prepare_database(BASE_DIR)

    state = "menu"
    username = "Player"
    leaderboard_data = []
    last_result = None

    def start_game_flow(base_name, fallback_best):
        nonlocal leaderboard_data

        safe_name = normalize_username(base_name)
        best = get_personal_best(BASE_DIR, safe_name) if db_ready else max(0, int(fallback_best))
        result = run_game(screen, clock, settings, safe_name, best, db_ready)

        if result["status"] in ("quit", "menu"):
            return result

        if db_ready:
            save_game_result(BASE_DIR, safe_name, result["score"], result["level"])
            leaderboard_data = load_leaderboard(BASE_DIR, 10)
            result["personal_best"] = max(result["personal_best"], get_personal_best(BASE_DIR, safe_name))

        return result

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        draw_menu_background(screen)

        if state == "menu":
            draw_center_text(screen, "TSIS4 SNAKE", title_font, WHITE, 52)
            draw_center_text(screen, "Database + Advanced Gameplay", tiny_font, MUTED, 78)

            draw_left_text(screen, "Username:", small_font, WHITE, 52, 98)
            name_box = pygame.Rect(150, 92, 198, 34)
            pygame.draw.rect(screen, (58, 63, 74), name_box, border_radius=8)
            pygame.draw.rect(screen, (108, 116, 134), name_box, 2, border_radius=8)
            typed = small_font.render(username + "_", True, WHITE)
            screen.blit(typed, (name_box.x + 8, name_box.y + 8))

            play_button = Button((110, 132, 180, 34), "Play", text_font)
            board_button = Button((110, 168, 180, 34), "Leaderboard", text_font)
            settings_button = Button((110, 204, 180, 34), "Settings", text_font)
            quit_button = Button((110, 240, 180, 34), "Quit", text_font)

            for button in (play_button, board_button, settings_button, quit_button):
                button.draw(screen)

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        result = start_game_flow(username, 0)
                        if result["status"] == "quit":
                            pygame.quit()
                            return
                        if result["status"] == "game_over":
                            last_result = result
                            username = result["username"]
                            state = "game_over"
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    elif event.unicode.isprintable() and len(username) < 16:
                        username += event.unicode

                if play_button.is_clicked(event):
                    result = start_game_flow(username, 0)
                    if result["status"] == "quit":
                        pygame.quit()
                        return
                    if result["status"] == "game_over":
                        last_result = result
                        username = result["username"]
                        state = "game_over"

                elif board_button.is_clicked(event):
                    leaderboard_data = load_leaderboard(BASE_DIR, 10) if db_ready else []
                    state = "leaderboard"
                elif settings_button.is_clicked(event):
                    state = "settings"
                elif quit_button.is_clicked(event):
                    pygame.quit()
                    return

        elif state == "leaderboard":
            draw_center_text(screen, "TOP 10 LEADERBOARD", title_font, WHITE, 50)

            if db_ready:
                y = 74
                header = "#  User            Score  Lvl  Date"
                draw_left_text(screen, header, tiny_font, MUTED, 28, y)
                y += 18

                if leaderboard_data:
                    for index, row in enumerate(leaderboard_data[:10], start=1):
                        line = (
                            f"{index:>2} {row['username'][:14]:<14} "
                            f"{row['score']:>5}  {row['level']:>3}  {format_played_at(row['played_at'])}"
                        )
                        draw_left_text(screen, line, tiny_font, WHITE, 22, y)
                        y += 18
                else:
                    draw_center_text(screen, "No records yet", text_font, MUTED, 170)
            else:
                draw_center_text(screen, "Database is unavailable", text_font, MUTED, 160)
                draw_center_text(screen, "Check database.ini and PostgreSQL", tiny_font, MUTED, 188)

            back_button = Button((110, 260, 180, 38), "Back", text_font)
            back_button.draw(screen)
            for event in events:
                if back_button.is_clicked(event) or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    state = "menu"

        elif state == "settings":
            draw_center_text(screen, "SETTINGS", title_font, WHITE, 56)

            draw_left_text(screen, f"Grid: {'ON' if settings['grid'] else 'OFF'}", text_font, WHITE, 50, 116)
            draw_left_text(screen, f"Sound: {'ON' if settings['sound'] else 'OFF'}", text_font, WHITE, 50, 152)
            draw_left_text(screen, "Snake color:", text_font, WHITE, 50, 188)
            pygame.draw.rect(screen, tuple(settings["snake_color"]), pygame.Rect(184, 189, 36, 24), border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(184, 189, 36, 24), 2, border_radius=6)

            grid_button = Button((250, 112, 100, 32), "Toggle", small_font)
            sound_button = Button((250, 148, 100, 32), "Toggle", small_font)
            color_button = Button((250, 184, 100, 32), "Change", small_font)
            save_back_button = Button((110, 250, 180, 38), "Save & Back", text_font)

            for button in (grid_button, sound_button, color_button, save_back_button):
                button.draw(screen)

            for event in events:
                if grid_button.is_clicked(event):
                    settings["grid"] = not settings["grid"]
                elif sound_button.is_clicked(event):
                    settings["sound"] = not settings["sound"]
                elif color_button.is_clicked(event):
                    settings["snake_color"] = cycle_color(settings["snake_color"])
                elif save_back_button.is_clicked(event):
                    settings = save_settings(BASE_DIR, settings)
                    state = "menu"
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "menu"

        elif state == "game_over":
            draw_center_text(screen, "GAME OVER", title_font, WHITE, 58)

            if last_result:
                draw_center_text(screen, f"Player: {last_result['username']}", text_font, WHITE, 118)
                draw_center_text(screen, f"Score: {last_result['score']}", text_font, WHITE, 146)
                draw_center_text(screen, f"Level reached: {last_result['level']}", text_font, WHITE, 174)
                draw_center_text(screen, f"Personal best: {last_result['personal_best']}", text_font, WHITE, 202)

            retry_button = Button((110, 228, 180, 32), "Retry", text_font)
            menu_button = Button((110, 264, 180, 32), "Main Menu", text_font)
            retry_button.draw(screen)
            menu_button.draw(screen)

            for event in events:
                if retry_button.is_clicked(event):
                    base_name = (last_result or {}).get("username", username)
                    base_best = (last_result or {}).get("personal_best", 0)
                    result = start_game_flow(base_name, base_best)

                    if result["status"] == "quit":
                        pygame.quit()
                        return
                    if result["status"] == "game_over":
                        last_result = result
                        username = result["username"]
                        state = "game_over"
                    else:
                        state = "menu"

                elif menu_button.is_clicked(event) or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    state = "menu"

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
