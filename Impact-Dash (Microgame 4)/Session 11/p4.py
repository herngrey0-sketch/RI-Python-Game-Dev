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
from tween import ease_out, lerp

# ─────────────────────────────────────────
#  INITIALISE pygame
# ─────────────────────────────────────────
pygame.init()

# ─────────────────────────────────────────
#  SCREEN / WINDOW SETUP
# ─────────────────────────────────────────
SCREEN_WIDTH  = 640
SCREEN_HEIGHT = 480
TITLE         = "Pygame"

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
PLAYER_SPEED = 5

targets = [
    pygame.Rect(200, 150, 30, 30),
    pygame.Rect(450, 300, 30, 30)
]

particles = []

# ─────────────────────────────────────────
#  VARIABLES
# ─────────────────────────────────────────
shake_offsets = []

# Tracks which screen is currently active
state = "menu"

font       = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 64)
popup_font = pygame.font.Font(None, 48)

# Pre-render the title surface so its width is known for centering
title_surf   = title_font.render("Impact Dash", True, WHITE)
title_w      = title_surf.get_width()
title_dest_x = (SCREEN_WIDTH - title_w) // 2   # pixel-perfect horizontal centre

menu_anim = 0.0  # Advances 0 → 1 each menu frame; drives the tween

# Each popup: { "value": str, "x": float, "y": float, "life": int, "max_life": int }
POPUP_LIFE  = 50   # frames the popup lives
POPUP_RISE  = 1.2  # pixels per frame it floats upward
score_popups = []

# ── DASH ───────────────────
dash_speed    = 18
dash_cooldown = 60
DASH_DURATION = 10          # frames of actual fast movement

dash_timer    = 0           # cooldown countdown
dash_active   = 0           # movement phase countdown
dir_x         = 0
dir_y         = 0

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

def draw_popups(surface):
    for popup in score_popups:
        # Alpha fades linearly from 255 → 0 over its lifetime
        alpha  = int(255 * (popup["life"] / popup["max_life"]))
        text_surf = popup_font.render(popup["value"], True, GREEN)
        # Blit onto a temporary surface so we can apply per-surface alpha
        tmp = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        tmp.blit(text_surf, (0, 0))
        tmp.set_alpha(alpha)
        # Centre the text on the popup's x position
        draw_x = int(popup["x"]) - text_surf.get_width() // 2
        draw_y = int(popup["y"])
        surface.blit(tmp, (draw_x, draw_y))

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
            # Escape key quits the game from any state
            if event.key == pygame.K_ESCAPE:
                running = False

            # Space bar on the menu transitions to gameplay
            if state == "menu" and event.key == pygame.K_SPACE:
                state = "gameplay"

    # ── UPDATE: MENU ─────────────────────
    if state == "menu":
        menu_anim = min(menu_anim + 0.02, 1.0)

    # ── UPDATE: GAMEPLAY ─────────────────
    elif state == "gameplay":

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            player.x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            player.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            player.y += PLAYER_SPEED

        if dash_timer == 0 and keys[pygame.K_LSHIFT]:
            dir_x = (1 if keys[pygame.K_RIGHT] else -1 if keys[pygame.K_LEFT] else 0)
            dir_y = (1 if keys[pygame.K_DOWN]  else -1 if keys[pygame.K_UP]   else 0)
            dash_timer  = dash_cooldown
            dash_active = DASH_DURATION
            spawn_particles(player.centerx, player.centery,
                            color=YELLOW, amount=40,
                            bias_x=-dir_x * 5, bias_y=-dir_y * 5)

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
            p["life"] -= 1
            if p["life"] <= 0:
                particles.remove(p)

        for t in targets[:]:
            if player.colliderect(t) and dash_active > 0:
                spawn_particles(t.centerx, t.centery, color=ORANGE, amount=40)
                shake_offsets = screen_shake()
                targets.remove(t)
                score_popups.append({
                    "value":    "+1",
                    "x":        float(t.centerx),
                    "y":        float(t.centery),
                    "life":     POPUP_LIFE,
                    "max_life": POPUP_LIFE,
                })

        # ── UPDATE: score popups ─────────
        for popup in score_popups[:]:
            popup["y"]    -= POPUP_RISE   # float upward each frame
            popup["life"] -= 1
            if popup["life"] <= 0:
                score_popups.remove(popup)

    # ── RENDER: MENU ─────────────────────────────────────────────────────────
    if state == "menu":
        screen.fill(BLACK)

        # Slide from fully off the left edge → horizontally centred.
        # ease_out gives a fast-start, soft-land feel.
        title_x = int(lerp(-title_w, title_dest_x, ease_out(menu_anim)))
        screen.blit(title_surf, (title_x, 150))

        # Prompt only appears once the title has (nearly) landed
        if menu_anim >= 0.9:
            start_surf = font.render("Press SPACE to start", True, (200, 200, 200))
            start_x    = (SCREEN_WIDTH - start_surf.get_width()) // 2
            screen.blit(start_surf, (start_x, 240))

        pygame.display.flip()
        clock.tick(FPS)

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

        pygame.draw.rect(game_surface, WHITE, player)

        for t in targets:
            pygame.draw.rect(game_surface, AMBER, t)

        # Draw floating score popups on top of everything else
        draw_popups(game_surface)

        ox, oy = shake_offsets.pop(0) if shake_offsets else (0, 0)
        screen.blit(game_surface, (ox, oy))

        pygame.display.flip()
        clock.tick(FPS)

# ─────────────────────────────────────────
#  CLEAN UP
# ─────────────────────────────────────────
pygame.quit()
sys.exit()