import math
import random
from pathlib import Path

import pygame

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
ROAD_LEFT = 40
ROAD_RIGHT = SCREEN_WIDTH - 40
LANE_COUNT = 4
LANE_X = [
    ROAD_LEFT + ((ROAD_RIGHT - ROAD_LEFT) * lane + (ROAD_RIGHT - ROAD_LEFT) / 2) / LANE_COUNT
    for lane in range(LANE_COUNT)
]

DIFFICULTY_PRESETS = {
    "easy": {
        "goal_distance": 1200,
        "base_speed": 220,
        "enemy_interval": 1.35,
        "obstacle_interval": 1.65,
        "event_interval": 3.4,
        "powerup_interval": 8.2,
        "coin_interval": 1.0,
    },
    "normal": {
        "goal_distance": 1650,
        "base_speed": 245,
        "enemy_interval": 1.1,
        "obstacle_interval": 1.4,
        "event_interval": 3.0,
        "powerup_interval": 7.2,
        "coin_interval": 0.9,
    },
    "hard": {
        "goal_distance": 2200,
        "base_speed": 280,
        "enemy_interval": 0.9,
        "obstacle_interval": 1.15,
        "event_interval": 2.5,
        "powerup_interval": 6.4,
        "coin_interval": 0.8,
    },
}


def _safe_load_image(path: Path, fallback_size, fallback_color):
    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        image = pygame.Surface(fallback_size, pygame.SRCALPHA)
        image.fill(fallback_color)
        return image

    return pygame.transform.smoothscale(image, fallback_size)


def _tint_surface(image, rgb):
    tinted = image.copy()
    tint_layer = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    tint_layer.fill((*rgb, 255))
    tinted.blit(tint_layer, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


def _choose_player_image(base_dir: Path, car_color):
    player_img = _safe_load_image(base_dir / "assets" / "images" / "Player.png", (52, 94), (68, 188, 255))
    enemy_img = _safe_load_image(base_dir / "assets" / "images" / "Enemy.png", (52, 94), (255, 82, 82))

    if car_color == "red":
        return enemy_img
    if car_color == "green":
        return _tint_surface(player_img, (120, 235, 140))
    return player_img


class Player(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midbottom=(LANE_X[1], SCREEN_HEIGHT - 20))
        self.lane_index = 1
        self.move_cooldown_ms = 120
        self.last_move_ms = 0

    def try_move(self, direction, now_ms):
        if now_ms - self.last_move_ms < self.move_cooldown_ms:
            return

        self.last_move_ms = now_ms
        self.lane_index = max(0, min(LANE_COUNT - 1, self.lane_index + direction))
        self.rect.centerx = int(LANE_X[self.lane_index])


class TrafficCar(pygame.sprite.Sprite):
    def __init__(self, lane_index, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midtop=(int(LANE_X[lane_index]), y))
        self.lane_index = lane_index
        self.speed_bonus = random.randint(30, 110)

    def update(self, world_speed, dt, _time_seconds):
        self.rect.y += int((world_speed + self.speed_bonus) * dt)
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


class Coin(pygame.sprite.Sprite):
    def __init__(self, lane_index, y):
        super().__init__()
        self.weight = random.randint(1, 5)
        size = 28
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 216, 66), (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, (212, 150, 10), (size // 2, size // 2), size // 2, 3)

        font = pygame.font.SysFont("Verdana", 16, bold=True)
        label = font.render(str(self.weight), True, (40, 30, 10))
        self.image.blit(label, label.get_rect(center=(size // 2, size // 2)))

        self.rect = self.image.get_rect(midtop=(int(LANE_X[lane_index]), y))
        self.lane_index = lane_index

    def update(self, world_speed, dt, _time_seconds):
        self.rect.y += int((world_speed + 40) * dt)
        if self.rect.top > SCREEN_HEIGHT + 10:
            self.kill()


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, lane_index, y, kind):
        super().__init__()
        self.kind = kind
        self.lane_index = lane_index

        if kind == "barrier":
            self.image = pygame.Surface((48, 28), pygame.SRCALPHA)
            self.image.fill((240, 86, 62))
            pygame.draw.rect(self.image, (255, 230, 40), (0, 10, 48, 8))
        elif kind == "oil":
            self.image = pygame.Surface((52, 26), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (28, 28, 28), (0, 0, 52, 26))
            pygame.draw.ellipse(self.image, (70, 70, 70), (6, 5, 14, 8))
        elif kind == "pothole":
            self.image = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (52, 52, 52), (18, 18), 16)
            pygame.draw.circle(self.image, (20, 20, 20), (18, 18), 10)
        elif kind == "speed_bump":
            self.image = pygame.Surface((52, 14), pygame.SRCALPHA)
            self.image.fill((244, 186, 44))
            pygame.draw.line(self.image, (30, 30, 30), (0, 4), (52, 4), 2)
            pygame.draw.line(self.image, (30, 30, 30), (0, 10), (52, 10), 2)
        elif kind == "moving_barrier":
            self.image = pygame.Surface((50, 24), pygame.SRCALPHA)
            self.image.fill((180, 50, 50))
            pygame.draw.rect(self.image, (0, 0, 0), (0, 0, 50, 24), 2)
        else:  # nitro_strip
            self.image = pygame.Surface((54, 14), pygame.SRCALPHA)
            self.image.fill((58, 225, 255))
            pygame.draw.line(self.image, (250, 250, 250), (5, 7), (49, 7), 2)

        self.rect = self.image.get_rect(midtop=(int(LANE_X[lane_index]), y))
        self.origin_x = self.rect.x
        self.phase = random.random() * math.pi

    def update(self, world_speed, dt, time_seconds):
        self.rect.y += int((world_speed + 30) * dt)

        if self.kind == "moving_barrier":
            offset = int(math.sin(time_seconds * 4 + self.phase) * 18)
            self.rect.x = self.origin_x + offset

        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, lane_index, y, kind):
        super().__init__()
        self.kind = kind
        self.spawn_time = pygame.time.get_ticks() / 1000.0
        self.ttl = 6.0

        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        palette = {
            "nitro": ((60, 222, 255), "N"),
            "shield": ((110, 226, 120), "S"),
            "repair": ((245, 195, 70), "R"),
        }
        color, label_text = palette[kind]

        pygame.draw.circle(self.image, color, (15, 15), 14)
        pygame.draw.circle(self.image, (15, 15, 15), (15, 15), 14, 2)
        font = pygame.font.SysFont("Verdana", 16, bold=True)
        label = font.render(label_text, True, (10, 10, 10))
        self.image.blit(label, label.get_rect(center=(15, 15)))

        self.rect = self.image.get_rect(midtop=(int(LANE_X[lane_index]), y))
        self.lane_index = lane_index

    def update(self, world_speed, dt, time_seconds):
        self.rect.y += int((world_speed + 20) * dt)
        if time_seconds - self.spawn_time > self.ttl or self.rect.top > SCREEN_HEIGHT + 10:
            self.kill()


def _draw_fallback_road(screen):
    screen.fill((94, 94, 94))
    pygame.draw.line(screen, (246, 226, 54), (ROAD_LEFT, 0), (ROAD_LEFT, SCREEN_HEIGHT), 2)
    pygame.draw.line(screen, (246, 226, 54), (ROAD_RIGHT, 0), (ROAD_RIGHT, SCREEN_HEIGHT), 2)

    for lane in range(1, LANE_COUNT):
        x = int(ROAD_LEFT + (ROAD_RIGHT - ROAD_LEFT) * lane / LANE_COUNT)
        for y in range(-20, SCREEN_HEIGHT, 80):
            pygame.draw.rect(screen, (230, 230, 230), (x - 4, y, 8, 42))


def run_game(screen, clock, settings, username):
    difficulty = str(settings.get("difficulty", "normal"))
    preset = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS["normal"])

    font_small = pygame.font.SysFont("Verdana", 18)
    font_tiny = pygame.font.SysFont("Verdana", 14)

    base_dir = Path(__file__).resolve().parent
    images_dir = base_dir / "assets" / "images"
    sounds_dir = base_dir / "assets" / "sounds"
    background_img = _safe_load_image(
        images_dir / "AnimatedStreet.png", (SCREEN_WIDTH, SCREEN_HEIGHT), (94, 94, 94)
    )
    enemy_image = _safe_load_image(images_dir / "Enemy.png", (50, 90), (250, 70, 70))
    player_image = _choose_player_image(base_dir, settings.get("car_color", "blue"))

    crash_sound = None
    if settings.get("sound", True):
        try:
            crash_sound = pygame.mixer.Sound(str(sounds_dir / "crash.wav"))
        except (pygame.error, FileNotFoundError):
            crash_sound = None

    player = Player(player_image)

    traffic = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    powerups = pygame.sprite.Group()

    enemy_timer = 0.0
    coin_timer = 0.0
    obstacle_timer = 0.0
    event_timer = 0.0
    powerup_timer = 0.0

    score = 0
    total_coins = 0
    distance = 0.0
    powerup_bonus = 0

    next_speed_coin_threshold = 10
    extra_speed_from_coins = 0

    active_powerup = None
    active_powerup_until = 0.0
    repair_charge = 0

    temporary_slow_until = 0.0
    strip_nitro_until = 0.0

    elapsed_time = 0.0
    road_scroll = 0.0

    def pick_safe_lane(avoid_player_lane=True):
        candidates = list(range(LANE_COUNT))
        random.shuffle(candidates)

        if avoid_player_lane and len(candidates) > 1:
            candidates = [lane for lane in candidates if lane != player.lane_index]

        if not candidates:
            candidates = list(range(LANE_COUNT))
            random.shuffle(candidates)

        for lane in candidates:
            blocked = False
            for group in (traffic, obstacles, coins, powerups):
                for sprite in group:
                    if getattr(sprite, "lane_index", None) == lane and sprite.rect.y < 140:
                        blocked = True
                        break
                if blocked:
                    break
            if not blocked:
                return lane

        return candidates[0]

    def spawn_traffic():
        lane = pick_safe_lane(avoid_player_lane=True)
        y = random.randint(-280, -120)
        traffic.add(TrafficCar(lane, y, enemy_image))

    def spawn_coin():
        lane = pick_safe_lane(avoid_player_lane=False)
        y = random.randint(-260, -80)
        coins.add(Coin(lane, y))

    def spawn_obstacle():
        lane = pick_safe_lane(avoid_player_lane=False)
        kind = random.choices(["barrier", "oil", "pothole"], weights=[4, 3, 3], k=1)[0]
        y = random.randint(-240, -100)
        obstacles.add(Obstacle(lane, y, kind))

    def spawn_event():
        lane = pick_safe_lane(avoid_player_lane=False)
        kind = random.choice(["moving_barrier", "speed_bump", "nitro_strip"])
        y = random.randint(-220, -110)
        obstacles.add(Obstacle(lane, y, kind))

    def spawn_powerup():
        lane = pick_safe_lane(avoid_player_lane=True)
        kind = random.choice(["nitro", "shield", "repair"])
        y = random.randint(-300, -120)
        powerups.add(PowerUp(lane, y, kind))

    def try_absorb_collision():
        nonlocal active_powerup, active_powerup_until, repair_charge, powerup_bonus

        if active_powerup == "shield":
            active_powerup = None
            active_powerup_until = 0.0
            powerup_bonus += 12
            return True

        if repair_charge > 0:
            repair_charge -= 1
            powerup_bonus += 10
            return True

        return False

    for _ in range(2):
        spawn_coin()
    spawn_traffic()

    while True:
        dt = clock.tick(60) / 1000.0
        now_ms = pygame.time.get_ticks()
        now = now_ms / 1000.0
        elapsed_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return {
                    "status": "quit",
                    "name": username,
                    "score": score,
                    "coins": total_coins,
                    "distance": int(distance),
                }

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return {
                        "status": "menu",
                        "name": username,
                        "score": score,
                        "coins": total_coins,
                        "distance": int(distance),
                    }
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    player.try_move(-1, now_ms)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    player.try_move(1, now_ms)

        progress = min(1.0, distance / preset["goal_distance"])
        interval_scale = max(0.52, 1.0 - 0.45 * progress)

        world_speed = preset["base_speed"] * (1.0 + 0.35 * progress) + extra_speed_from_coins

        if active_powerup == "nitro":
            if now <= active_powerup_until:
                world_speed *= 1.5
            else:
                active_powerup = None

        if now < strip_nitro_until:
            world_speed *= 1.35

        if now < temporary_slow_until:
            world_speed *= 0.72

        enemy_timer += dt
        coin_timer += dt
        obstacle_timer += dt
        event_timer += dt
        powerup_timer += dt

        if enemy_timer >= preset["enemy_interval"] * interval_scale:
            spawn_traffic()
            enemy_timer = 0.0

        if coin_timer >= preset["coin_interval"] * interval_scale:
            spawn_coin()
            coin_timer = 0.0

        if obstacle_timer >= preset["obstacle_interval"] * interval_scale:
            spawn_obstacle()
            obstacle_timer = 0.0

        if event_timer >= preset["event_interval"] * interval_scale:
            spawn_event()
            event_timer = 0.0

        if powerup_timer >= preset["powerup_interval"] * interval_scale:
            spawn_powerup()
            powerup_timer = 0.0

        for group in (traffic, coins, obstacles, powerups):
            for sprite in group:
                sprite.update(world_speed, dt, elapsed_time)

        for coin in pygame.sprite.spritecollide(player, coins, dokill=True):
            total_coins += coin.weight

        while total_coins >= next_speed_coin_threshold:
            extra_speed_from_coins += 18
            next_speed_coin_threshold += 10

        for item in pygame.sprite.spritecollide(player, powerups, dokill=True):
            if active_powerup is not None:
                continue

            if item.kind == "nitro":
                active_powerup = "nitro"
                active_powerup_until = now + random.uniform(3.0, 5.0)
                powerup_bonus += 30
            elif item.kind == "shield":
                active_powerup = "shield"
                active_powerup_until = float("inf")
                powerup_bonus += 22
            elif item.kind == "repair":
                repair_charge = 1
                powerup_bonus += 16

        for obstacle in pygame.sprite.spritecollide(player, obstacles, dokill=False):
            if obstacle.kind in ("barrier", "moving_barrier"):
                if try_absorb_collision():
                    obstacle.kill()
                    continue

                if crash_sound:
                    crash_sound.play()
                final_score = score
                return {
                    "status": "crashed",
                    "name": username,
                    "score": final_score,
                    "coins": total_coins,
                    "distance": int(distance),
                }

            if obstacle.kind == "oil":
                temporary_slow_until = max(temporary_slow_until, now + 1.8)
                obstacle.kill()
            elif obstacle.kind == "pothole":
                total_coins = max(0, total_coins - 2)
                temporary_slow_until = max(temporary_slow_until, now + 0.9)
                obstacle.kill()
            elif obstacle.kind == "speed_bump":
                temporary_slow_until = max(temporary_slow_until, now + 1.1)
                obstacle.kill()
            elif obstacle.kind == "nitro_strip":
                strip_nitro_until = max(strip_nitro_until, now + 2.2)
                obstacle.kill()

        for enemy in pygame.sprite.spritecollide(player, traffic, dokill=False):
            if try_absorb_collision():
                enemy.kill()
                continue

            if crash_sound:
                crash_sound.play()
            final_score = score
            return {
                "status": "crashed",
                "name": username,
                "score": final_score,
                "coins": total_coins,
                "distance": int(distance),
            }

        distance += world_speed * dt * 0.18
        score = total_coins * 12 + int(distance) + powerup_bonus

        if distance >= preset["goal_distance"]:
            score += 200
            return {
                "status": "finished",
                "name": username,
                "score": score,
                "coins": total_coins,
                "distance": int(distance),
            }

        road_scroll = (road_scroll + world_speed * dt) % SCREEN_HEIGHT
        screen.blit(background_img, (0, int(road_scroll) - SCREEN_HEIGHT))
        screen.blit(background_img, (0, int(road_scroll)))

        if background_img.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
            _draw_fallback_road(screen)

        for group in (coins, powerups, obstacles, traffic):
            group.draw(screen)
        screen.blit(player.image, player.rect)

        hud = pygame.Surface((SCREEN_WIDTH, 92), pygame.SRCALPHA)
        hud.fill((10, 10, 10, 150))
        screen.blit(hud, (0, 0))

        remaining = max(0, int(preset["goal_distance"] - distance))
        hud_lines = [
            f"Player: {username[:16]}",
            f"Score: {score}   Coins: {total_coins}",
            f"Distance: {int(distance)}   Left: {remaining}",
            f"Difficulty: {difficulty}",
        ]

        if active_powerup == "nitro":
            seconds_left = max(0.0, active_powerup_until - now)
            hud_lines.append(f"Power-up: Nitro ({seconds_left:.1f}s)")
        elif active_powerup == "shield":
            hud_lines.append("Power-up: Shield (until hit)")
        elif repair_charge > 0:
            hud_lines.append("Power-up: Repair ready")
        else:
            hud_lines.append("Power-up: none")

        if now < strip_nitro_until:
            hud_lines.append("Road event: Nitro strip boost")
        elif now < temporary_slow_until:
            hud_lines.append("Road event: Slow zone")
        else:
            hud_lines.append("Road event: normal")

        for index, line in enumerate(hud_lines):
            render_font = font_small if index < 4 else font_tiny
            label = render_font.render(line, True, (240, 240, 240))
            screen.blit(label, (10, 8 + index * 14))

        pygame.display.flip()
