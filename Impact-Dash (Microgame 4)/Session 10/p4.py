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
GREEN = (0, 255, 0)
RED = (255, 0, 0)
AMBER = (255, 180, 0)
ORANGE = (255,100, 0)

# ─────────────────────────────────────────
#  GAME OBJECTS
# ─────────────────────────────────────────

# Player — white square, starts near top-left
# pygame.Rect(x, y, width, height)
player = pygame.Rect(100, 100, 40, 40)
PLAYER_SPEED = 5

targets =[
    pygame.Rect(200, 150, 30, 30),
    pygame.Rect(450, 300, 30, 30)
]

particles = []

# ─────────────────────────────────────────
#  VARIABLES
# ─────────────────────────────────────────
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
# Draw a simple grid (optional visual)
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

    # ── UPDATE ───────────────────────────

    # 1. Read keyboard input & move player
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        player.x -= PLAYER_SPEED
    if keys[pygame.K_RIGHT]:
        player.x += PLAYER_SPEED
    if keys[pygame.K_UP]:
        player.y -= PLAYER_SPEED      # NOTE: UP decreases y in pygame
    if keys[pygame.K_DOWN]:
        player.y += PLAYER_SPEED
    
    if dash_timer == 0 and keys[pygame.K_LSHIFT]:
        dir_x = (1 if keys[pygame.K_RIGHT] else -1 if keys[pygame.K_LEFT] else 0)
        dir_y = (1 if keys[pygame.K_DOWN]  else -1 if keys[pygame.K_UP]   else 0)
        dash_timer  = dash_cooldown
        dash_active = DASH_DURATION
        # Initial burst particles
        spawn_particles(player.centerx, player.centery,
                        color=YELLOW, amount=40,
                        bias_x=-dir_x * 5, bias_y=-dir_y * 5)

    # Apply movement every frame of the active phase
    if dash_active > 0:
        player.x += dir_x * dash_speed
        player.y += dir_y * dash_speed
        dash_active -= 1
        # Trail every active frame
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
            targets.remove(t)

    # ── RENDER ───────────────────────────

    # 1. Clear the screen
    screen.fill(BLACK)

    # 2. Optional subtle grid
    draw_grid(screen)

    for p in particles:
        pygame.draw.circle(screen, p["color"],
                           (int(p["pos"][0]), int(p["pos"][1])), 3)
        
    # 3. Draw the player
    pygame.draw.rect(screen, WHITE, player)

    for t in targets:
        pygame.draw.rect(screen, AMBER, t)

    # 4. Flip / update the display
    pygame.display.flip()

    # 5. Tick the clock (cap at FPS)
    clock.tick(FPS)

# ─────────────────────────────────────────
#  CLEAN UP
# ─────────────────────────────────────────
pygame.quit()
sys.exit()