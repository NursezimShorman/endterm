from pathlib import Path

import pygame

from persistence import (
    ALLOWED_COLORS,
    ALLOWED_DIFFICULTIES,
    add_leaderboard_entry,
    load_leaderboard,
    load_settings,
    save_settings,
)
from racer import SCREEN_HEIGHT, SCREEN_WIDTH, run_game
from ui import BG, BLACK, MUTED, WHITE, Button, draw_center_text, draw_left_text, draw_panel

BASE_DIR = Path(__file__).resolve().parent


def apply_music_setting(settings, mixer_ready):
    if not mixer_ready:
        return

    music_path = BASE_DIR / "assets" / "sounds" / "background.wav"
    if not settings.get("sound", True):
        pygame.mixer.music.stop()
        return

    try:
        pygame.mixer.music.load(str(music_path))
        pygame.mixer.music.play(-1)
    except (pygame.error, FileNotFoundError):
        pass


def cycle_value(current, options):
    index = options.index(current)
    return options[(index + 1) % len(options)]


def draw_background(screen):
    screen.fill(BG)
    draw_panel(screen, pygame.Rect(20, 24, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 48))


def main():
    pygame.init()
    mixer_ready = True
    try:
        pygame.mixer.init()
    except pygame.error:
        mixer_ready = False

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Racer")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("Verdana", 36, bold=True)
    text_font = pygame.font.SysFont("Verdana", 22)
    small_font = pygame.font.SysFont("Verdana", 18)

    settings = load_settings(BASE_DIR)
    leaderboard = load_leaderboard(BASE_DIR)
    apply_music_setting(settings, mixer_ready)

    state = "menu"
    username = "Player"
    last_result = None

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        draw_background(screen)

        if state == "menu":
            draw_center_text(screen, "TSIS3 RACER", title_font, WHITE, 95)
            draw_center_text(screen, "Advanced Driving, Leaderboard & Power-Ups", small_font, MUTED, 128)

            play_button = Button((120, 190, 160, 48), "Play", text_font)
            board_button = Button((120, 250, 160, 48), "Leaderboard", text_font)
            settings_button = Button((120, 310, 160, 48), "Settings", text_font)
            quit_button = Button((120, 370, 160, 48), "Quit", text_font)

            for button in (play_button, board_button, settings_button, quit_button):
                button.draw(screen)

            for event in events:
                if play_button.is_clicked(event):
                    state = "username"
                elif board_button.is_clicked(event):
                    leaderboard = load_leaderboard(BASE_DIR)
                    state = "leaderboard"
                elif settings_button.is_clicked(event):
                    state = "settings"
                elif quit_button.is_clicked(event):
                    pygame.quit()
                    return

        elif state == "username":
            draw_center_text(screen, "Enter Username", title_font, WHITE, 110)
            draw_center_text(screen, "Press Enter to start, Esc to go back", small_font, MUTED, 148)

            name_box = pygame.Rect(70, 240, 260, 56)
            pygame.draw.rect(screen, (56, 60, 72), name_box, border_radius=10)
            pygame.draw.rect(screen, (118, 124, 142), name_box, 2, border_radius=10)

            typed = small_font.render(username + "_", True, WHITE)
            screen.blit(typed, (name_box.x + 14, name_box.y + 18))

            start_button = Button((120, 340, 160, 46), "Start", text_font)
            back_button = Button((120, 396, 160, 46), "Back", text_font)
            start_button.draw(screen)
            back_button.draw(screen)

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
                    elif event.key == pygame.K_RETURN:
                        username = username.strip() or "Player"
                        result = run_game(screen, clock, settings, username)
                        if result["status"] == "quit":
                            pygame.quit()
                            return
                        if result["status"] == "menu":
                            state = "menu"
                        else:
                            leaderboard = add_leaderboard_entry(BASE_DIR, result)
                            last_result = result
                            state = "game_over"
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    elif event.unicode.isprintable() and len(username) < 16:
                        username += event.unicode

                if start_button.is_clicked(event):
                    username = username.strip() or "Player"
                    result = run_game(screen, clock, settings, username)
                    if result["status"] == "quit":
                        pygame.quit()
                        return
                    if result["status"] == "menu":
                        state = "menu"
                    else:
                        leaderboard = add_leaderboard_entry(BASE_DIR, result)
                        last_result = result
                        state = "game_over"

                if back_button.is_clicked(event):
                    state = "menu"

        elif state == "settings":
            draw_center_text(screen, "Settings", title_font, WHITE, 98)

            draw_left_text(screen, f"Sound: {'ON' if settings['sound'] else 'OFF'}", text_font, WHITE, 60, 190)
            draw_left_text(screen, f"Car color: {settings['car_color'].capitalize()}", text_font, WHITE, 60, 250)
            draw_left_text(screen, f"Difficulty: {settings['difficulty'].capitalize()}", text_font, WHITE, 60, 310)

            sound_button = Button((260, 185, 90, 38), "Toggle", small_font)
            color_button = Button((260, 245, 90, 38), "Change", small_font)
            difficulty_button = Button((260, 305, 90, 38), "Change", small_font)
            back_button = Button((120, 420, 160, 46), "Back", text_font)

            for button in (sound_button, color_button, difficulty_button, back_button):
                button.draw(screen)

            for event in events:
                if sound_button.is_clicked(event):
                    settings["sound"] = not settings["sound"]
                    settings = save_settings(BASE_DIR, settings)
                    apply_music_setting(settings, mixer_ready)

                if color_button.is_clicked(event):
                    settings["car_color"] = cycle_value(settings["car_color"], list(ALLOWED_COLORS))
                    settings = save_settings(BASE_DIR, settings)

                if difficulty_button.is_clicked(event):
                    settings["difficulty"] = cycle_value(settings["difficulty"], list(ALLOWED_DIFFICULTIES))
                    settings = save_settings(BASE_DIR, settings)

                if back_button.is_clicked(event):
                    state = "menu"

        elif state == "leaderboard":
            draw_center_text(screen, "Leaderboard Top 10", title_font, WHITE, 90)

            y = 150
            if leaderboard:
                for idx, row in enumerate(leaderboard[:10], start=1):
                    line = (
                        f"{idx:>2}. {row['name']:<16} "
                        f"Score: {row['score']:<5} Dist: {row['distance']:<5} Coins: {row['coins']}"
                    )
                    draw_left_text(screen, line, small_font, WHITE, 32, y)
                    y += 33
            else:
                draw_center_text(screen, "No records yet", text_font, MUTED, 280)

            back_button = Button((120, 520, 160, 46), "Back", text_font)
            back_button.draw(screen)

            for event in events:
                if back_button.is_clicked(event) or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    state = "menu"

        elif state == "game_over":
            title = "Finish" if last_result and last_result["status"] == "finished" else "Game Over"
            draw_center_text(screen, title, title_font, WHITE, 92)

            if last_result:
                draw_center_text(screen, f"Player: {last_result['name']}", text_font, WHITE, 182)
                draw_center_text(screen, f"Score: {last_result['score']}", text_font, WHITE, 222)
                draw_center_text(screen, f"Distance: {last_result['distance']}", text_font, WHITE, 262)
                draw_center_text(screen, f"Coins: {last_result['coins']}", text_font, WHITE, 302)

            retry_button = Button((120, 390, 160, 46), "Retry", text_font)
            menu_button = Button((120, 448, 160, 46), "Main Menu", text_font)
            retry_button.draw(screen)
            menu_button.draw(screen)

            for event in events:
                if retry_button.is_clicked(event):
                    base_name = (last_result or {}).get("name", username)
                    result = run_game(screen, clock, settings, base_name)
                    if result["status"] == "quit":
                        pygame.quit()
                        return
                    if result["status"] == "menu":
                        state = "menu"
                    else:
                        leaderboard = add_leaderboard_entry(BASE_DIR, result)
                        last_result = result

                if menu_button.is_clicked(event):
                    state = "menu"

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
