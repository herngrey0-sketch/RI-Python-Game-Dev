# new additions = timer, high_score, charging_up_bar, circle around player, increase in level

import os
import sys


# ── Headless / Codespaces environment fixes ───────────────────────────────────
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"


if not os.environ.get("XDG_RUNTIME_DIR"):
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-vscode"
    os.makedirs("/tmp/runtime-vscode", exist_ok=True)


os.environ["SDL_AUDIODRIVER"] = "dummy"


import pygame
import random
from feedback import screen_shake

# ─────────────────────────────────────────
#  INITIALISE pygame
# ─────────────────────────────────────────
pygame.init()


# ─────────────────────────────────────────
#  SCREEN / WINDOW SETUP
# ─────────────────────────────────────────
SCREEN_WIDTH  = 640
SCREEN_HEIGHT = 480
TITLE         = "Impact Dash"


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)


# ─────────────────────────────────────────
#  CLOCK  (controls frames-per-second)
# ─────────────────────────────────────────
clock = pygame.time.Clock()
FPS = 60


# ─────────────────────────────────────────
#  COLOURS  (R, G, B)
# ─────────────────────────────────────────
BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
GRAY   = ( 40,  40,  40)
YELLOW = (255, 255, 0)
GREEN  = (  0, 255, 0)
RED    = (255,   0, 0)
AMBER  = (255, 180, 0)
ORANGE = (255, 100, 0)


# ─────────────────────────────────────────
#  GAME OBJECTS
# ─────────────────────────────────────────
player = pygame.Rect(100, 100, 40, 40)
PLAYER_SPEED = 6
DASH_READY_GLOW = 0.0


HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "high_score.txt")


def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(value):
    with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as file:
        file.write(str(value))


def spawn_target():
    target_w = 30
    target_h = 30
    padding = 30
    max_attempts = 200

    for _ in range(max_attempts):
        x = random.randint(padding, SCREEN_WIDTH - target_w - padding)
        y = random.randint(padding, SCREEN_HEIGHT - target_h - padding)
        rect = pygame.Rect(x, y, target_w, target_h)

        if not rect.colliderect(player):
            if all(not rect.colliderect(existing) for existing in targets):
                return rect

    return pygame.Rect(
        random.randint(padding, SCREEN_WIDTH - target_w - padding),
        random.randint(padding, SCREEN_HEIGHT - target_h - padding),
        target_w,
        target_h,
    )


targets = []
DIFFICULTY_SCALE = 0.0


particles = []


# ─────────────────────────────────────────
#  VARIABLES
# ─────────────────────────────────────────
shake_offsets = []

score = 0
TIME_LIMIT = 30
time_left = TIME_LIMIT
high_score = load_high_score()

state = "menu"


game_over_message = ""
game_over_color = YELLOW
game_over_timer = 0
game_over_done = False


font       = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 64)
popup_font = pygame.font.Font(None, 48)


title_surf   = title_font.render("Impact Dash", True, WHITE)
title_w      = title_surf.get_width()
title_dest_x = (SCREEN_WIDTH - title_w) // 2


menu_anim = 0.0


POPUP_LIFE = 50
POPUP_RISE = 1.2
score_popups = []


# ── DASH ─────────────────────────────────
dash_speed    = 18
dash_cooldown = 60
DASH_DURATION = 10
MAX_CHARGE    = 25


dash_timer  = 0
dash_active = 0
dir_x       = 0
dir_y       = 0


charging    = False
charge_time = 0


# ── TRANSITIONS ──────────────────────────
# fade_dir: +1 = fading to black, -1 = fading from black, 0 = stable
FADE_SPEED   = 8           # alpha units per frame
fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
fade_surface.fill(BLACK)
fade_alpha   = 255          # start fully black so the menu fades in on launch
fade_dir     = -1           # immediately begin fading in
pending_state = None        # state to switch to once fade-out completes


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def draw_grid(surface):
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(surface, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(surface, GRAY, (0, y), (SCREEN_WIDTH, y))


def spawn_particles(x, y, color=YELLOW, amount=20, bias_x=0, bias_y=0):
    for _ in range(amount):
        particles.append({
            "pos":   [x, y],
            "vel":   [random.randint(-3, 3) + bias_x,
                      random.randint(-3, 3) + bias_y],
            "color": color,
            "life":  random.randint(20, 40)
        })

def lerp(a, b, t):
    return a + (b - a) * t


def easeout(t):
    return 1 - (1 - t) ** 3

def draw_popups(surface):
    for popup in score_popups:
        alpha     = int(255 * (popup["life"] / popup["max_life"]))
        text_surf = popup_font.render(popup["value"], True, GREEN)
        tmp       = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        tmp.blit(text_surf, (0, 0))
        tmp.set_alpha(alpha)
        draw_x = int(popup["x"]) - text_surf.get_width() // 2
        draw_y = int(popup["y"])
        surface.blit(tmp, (draw_x, draw_y))


def draw_player(surface, rect, charging, charge_t, dash_ready_glow):
    cx, cy = rect.centerx, rect.centery
    if dash_timer == 0 and dash_active == 0:
        glow_radius = 50 + int(10 * dash_ready_glow)
        glow_color = (100 + int(155 * dash_ready_glow), 100 + int(155 * dash_ready_glow), 0)
        pygame.draw.circle(surface, glow_color, (cx, cy), glow_radius, 2)
    if not charging:
        pygame.draw.rect(surface, WHITE, rect)
        pygame.draw.rect(surface, (100, 200, 255) if dash_timer == 0 and dash_active == 0 else GRAY, rect, 2)
        return
    t = min(charge_t / MAX_CHARGE, 1.0)
    w = int(rect.width  * lerp(1.0, 0.70, t))
    h = int(rect.height * lerp(1.0, 1.20, t))
    squished = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    pygame.draw.rect(surface, (255, 200, 0), squished)
    charge_bar_y = cy + 35
    bar_width = int(40 * t)
    pygame.draw.rect(surface, (100, 100, 100), (cx - 20, charge_bar_y, 40, 6))
    pygame.draw.rect(surface, YELLOW, (cx - 20, charge_bar_y, bar_width, 6))


def start_transition(target_state):
    """Begin fading to black; switch to target_state at peak."""
    global fade_dir, pending_state
    fade_dir      = +1
    pending_state = target_state


def reset_game_state():
    global score, time_left, targets, player, game_over_message, game_over_color, game_over_timer, game_over_done, DIFFICULTY_SCALE, DASH_READY_GLOW

    score = 0
    time_left = TIME_LIMIT
    player.x = SCREEN_WIDTH // 2
    player.y = SCREEN_HEIGHT // 2
    targets.clear()
    DIFFICULTY_SCALE = 0.0
    DASH_READY_GLOW = 0.0
    game_over_message = ""
    game_over_color = YELLOW
    game_over_timer = 0
    game_over_done = False
    for _ in range(3):
        targets.append(spawn_target())


# ─────────────────────────────────────────
#  GAME LOOP
# ─────────────────────────────────────────
running = True


while running:


    # ── EVENT HANDLING ───────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # Only accept SPACE when fully visible and not mid-transition
            if state == "menu" and event.key == pygame.K_SPACE and fade_dir == 0:
                start_transition("gameplay")


        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LSHIFT and charging:
                live_keys = pygame.key.get_pressed()
                dir_x = (1 if live_keys[pygame.K_RIGHT] else -1 if live_keys[pygame.K_LEFT] else 0)
                dir_y = (1 if live_keys[pygame.K_DOWN]  else -1 if live_keys[pygame.K_UP]   else 0)
                charging    = False
                charge_time = 0
                dash_timer  = dash_cooldown
                dash_active = DASH_DURATION
                spawn_particles(player.centerx, player.centery,
                                color=YELLOW, amount=40,
                                bias_x=-dir_x * 5, bias_y=-dir_y * 5)


    # ── UPDATE: FADE ─────────────────────
    fade_alpha += FADE_SPEED * fade_dir
    if fade_dir == +1 and fade_alpha >= 255:
        # Peak of fade-out: commit the state switch and start fading back in
        fade_alpha    = 255
        fade_dir      = -1
        state         = pending_state
        if state == "gameplay":
            reset_game_state()
        pending_state = None
    elif fade_dir == -1 and fade_alpha <= 0:
        # Fully visible again: stop animating
        fade_alpha = 0
        fade_dir   = 0


    # ── UPDATE: MENU ─────────────────────
    if state == "menu":
        menu_anim = min(menu_anim + 0.02, 1.0)


    # ── UPDATE: GAMEPLAY ─────────────────
    elif state == "gameplay":
        DIFFICULTY_SCALE = min(score * 0.15, 3.0)
        if dash_timer == 0 and dash_active == 0:
            DASH_READY_GLOW = (DASH_READY_GLOW + 0.08) % 1.0
        else:
            DASH_READY_GLOW = 0.0

        if not game_over_done:
            if time_left > 0:
                time_left = max(0.0, time_left - 1 / FPS)

            if time_left <= 0:
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
                    game_over_message = "A New High Score!"
                    game_over_color = YELLOW
                else:
                    game_over_message = "You Didn't Beat Your High Score :("
                    game_over_color = RED
                game_over_timer = 120
                game_over_done = True
                spawn_particles(player.centerx, player.centery, color=YELLOW, amount=50)

        else:
            game_over_timer -= 1
            if game_over_timer <= 0 and fade_dir == 0:
                start_transition("menu")

        keys = pygame.key.get_pressed()


        if keys[pygame.K_LEFT]:  player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]: player.x += PLAYER_SPEED
        if keys[pygame.K_UP]:    player.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:  player.y += PLAYER_SPEED


        if dash_timer == 0 and keys[pygame.K_LSHIFT] and dash_active == 0:
            charging = True
            if charge_time % 4 == 0:
                spawn_particles(player.centerx, player.centery,
                                color=AMBER, amount=2)
            charge_time = min(charge_time + 1, MAX_CHARGE)


        if dash_active > 0:
            player.x += dir_x * dash_speed
            player.y += dir_y * dash_speed
            dash_active -= 1
            spawn_particles(player.centerx - dir_x * 15,
                            player.centery - dir_y * 15,
                            color=YELLOW, amount=6,
                            bias_x=-dir_x * 3, bias_y=-dir_y * 3)


        if dash_timer > 0:
            dash_timer -= 1


        player.clamp_ip(screen.get_rect())


        for p in particles[:]:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["life"]   -= 1
            if p["life"] <= 0:
                particles.remove(p)


        # Spawn more targets as difficulty increases
        target_count = 3 + int(DIFFICULTY_SCALE)
        while len(targets) < target_count and random.random() < 0.08 + DIFFICULTY_SCALE * 0.02:
            targets.append(spawn_target())

        for t in targets[:]:
            if time_left > 0 and player.colliderect(t) and dash_active > 0:
                spawn_particles(t.centerx, t.centery, color=ORANGE, amount=50)
                shake_offsets = screen_shake()
                targets.remove(t)
                score += 1
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
                if len(targets) < target_count:
                    targets.append(spawn_target())
                score_popups.append({
                    "value":    "+1",
                    "x":        float(t.centerx),
                    "y":        float(t.centery),
                    "life":     POPUP_LIFE,
                    "max_life": POPUP_LIFE,
                })


        for popup in score_popups[:]:
            popup["y"]    -= POPUP_RISE
            popup["life"] -= 1
            if popup["life"] <= 0:
                score_popups.remove(popup)


    # ── RENDER: MENU ─────────────────────────────────────────────────────────
    if state == "menu":
        screen.fill(BLACK)


        title_x = int(lerp(-title_w, title_dest_x, easeout(menu_anim)))
        screen.blit(title_surf, (title_x, 150))


        if menu_anim >= 0.9:
            start_surf = font.render("Press SPACE to start", True, (200, 200, 200))
            start_x    = (SCREEN_WIDTH - start_surf.get_width()) // 2
            screen.blit(start_surf, (start_x, 240))

        high_score_surf = font.render(f"High Score: {high_score}", True, YELLOW)
        high_score_x = (SCREEN_WIDTH - high_score_surf.get_width()) // 2
        screen.blit(high_score_surf, (high_score_x, 290))


    # ── RENDER: GAMEPLAY ─────────────────────────────────────────────────────
    elif state == "gameplay":
        screen.fill(BLACK)
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        game_surface.fill(BLACK)
        draw_grid(game_surface)


        bar_fill  = int(200 * (1 - dash_timer / dash_cooldown)) if dash_timer > 0 else 200
        bar_color = GREEN if dash_timer == 0 else RED
        pygame.draw.rect(game_surface, GRAY,      (20, SCREEN_HEIGHT - 20, 200, 12))
        pygame.draw.rect(game_surface, bar_color, (20, SCREEN_HEIGHT - 20, bar_fill, 12))


        for p in particles:
            pygame.draw.circle(game_surface, p["color"],
                               (int(p["pos"][0]), int(p["pos"][1])), 3)


        score_text = font.render(f"Score: {score}", True, WHITE)
        timer_text = font.render(f"Time: {max(0, int(time_left))}", True, WHITE)
        difficulty_text = font.render(f"Lvl: {min(6, int(DIFFICULTY_SCALE) + 1)}", True, (100, 200, 255))
        game_surface.blit(score_text, (20, 20))
        game_surface.blit(timer_text, (SCREEN_WIDTH - timer_text.get_width() - 20, 20))
        game_surface.blit(difficulty_text, (SCREEN_WIDTH // 2 - difficulty_text.get_width() // 2, 20))

        draw_player(game_surface, player, charging, charge_time, DASH_READY_GLOW)


        if game_over_done:
            message_alpha = int(255 * (1 - abs(game_over_timer - 60) / 60))
            message_surf = title_font.render(game_over_message, True, game_over_color)
            message_tmp = pygame.Surface(message_surf.get_size(), pygame.SRCALPHA)
            message_tmp.blit(message_surf, (0, 0))
            message_tmp.set_alpha(message_alpha)
            message_x = (SCREEN_WIDTH - message_surf.get_width()) // 2
            message_y = SCREEN_HEIGHT // 2 - 40
            screen.blit(message_tmp, (message_x, message_y))

        for t in targets:
            pygame.draw.rect(game_surface, AMBER, t)


        draw_popups(game_surface)


        ox, oy = shake_offsets.pop(0) if shake_offsets else (0, 0)
        screen.blit(game_surface, (ox, oy))


    # ── RENDER: FADE OVERLAY ─────────────────────────────────────────────────
    # Drawn on top of every state — a single shared black surface with variable alpha
    if fade_alpha > 0:
        fade_surface.set_alpha(fade_alpha)
        screen.blit(fade_surface, (0, 0))


    # ── FLIP / TICK ──────────────────────────────────────────────────────────
    pygame.display.flip()
    clock.tick(FPS)


# ─────────────────────────────────────────
#  CLEAN UP
# ─────────────────────────────────────────
pygame.quit()
sys.exit()

