import os
import sys

# ── Headless / Codespaces environment fixes ───────────────────────────────────
# Xvfb virtual display (started by postStartCommand)
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"

# Suppress the "XDG_RUNTIME_DIR is invalid" warning
if not os.environ.get("XDG_RUNTIME_DIR"):
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-vscode"
    os.makedirs("/tmp/runtime-vscode", exist_ok=True)

# Tell SDL to use a dummy audio driver — silences all ALSA "no sound card" errors
# (Codespaces has no audio hardware; this is safe and expected)
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

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
RED    = (255,   0,   0)
GREEN = (0,   255,   0)
GRAY   = ( 40,  40,  40)   # subtle grid / background tint

font = pygame.font.Font(None, 36)
# ─────────────────────────────────────────
#  GAME OBJECTS & VARIABLES
# ─────────────────────────────────────────

# Player  — white square, starts near top-left
player = pygame.Rect(100, 100, 40, 40)
PLAYER_SPEED = 5

# Enemy   — red square, starts centre-right
enemy = pygame.Rect(300, 200, 40, 40)
ENEMY_SPEED = 3

collectibles = [
    pygame.Rect(300, 100, 20, 20),
    pygame.Rect(500, 300, 20, 20)
]

hazards = [
    pygame.Rect(400, 150, 30, 30),
]

# Add more hazards
# hazards.append(pygame.Rect(600, 250, 30, 30))

score = 0

# ─────────────────────────────────────────
#  HELPER: draw a simple grid (optional visual)
# ─────────────────────────────────────────
def draw_grid():
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

# ─────────────────────────────────────────
#  GAME LOOP
# ─────────────────────────────────────────
running = True
game_over = False

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
        player.y -= PLAYER_SPEED          # NOTE: UP decreases y in pygame
    if keys[pygame.K_DOWN]:
        player.y += PLAYER_SPEED

    # 2. Keep player inside the window
    player.clamp_ip(screen.get_rect())

    # 3. Move enemy left; wrap around when off-screen
    # enemy.x -= ENEMY_SPEED
    # if enemy.right < 0:
    #     enemy.x = SCREEN_WIDTH
    
    for c in collectibles[:]:
        if player.colliderect(c):
            collectibles.remove(c)
            score += 1

            screen.fill(GREEN)
            pygame.display.flip()
            pygame.time.delay(60)
    
    # Hazard movement
    for h in hazards:
        h.x -= 3
        if h.x < -30:
            h.x = SCREEN_WIDTH
        h.y += 2
        if h.y > SCREEN_HEIGHT:
            h.y = 0
    
    # Hazard 
    for h in hazards:
        if player.colliderect(h):
            player.x, player.y = 100, 200
            game_over = True

    if game_over:
        # Screen flash
        screen.fill(RED)
        pygame.display.flip()
        pygame.time.delay(100)

        # Reset game
        player.x, player.y = 100, 200
        score = 0
        collectibles = [
            pygame.Rect(300, 100, 20, 20),
            pygame.Rect(500, 300, 20, 20)
        ]

        game_over = False

    # ── RENDER ───────────────────────────

    # 1. Clear the screen
    screen.fill(BLACK)

    # 2. Optional subtle grid
    draw_grid()

    # 3. Draw game objects
    pygame.draw.rect(screen, WHITE, player)   # player
    # pygame.draw.rect(screen, RED,   enemy)    # enemy

    for c in collectibles:
        pygame.draw.rect(screen, GREEN, c)

    for h in hazards:
        pygame.draw.rect(screen, RED, h)
    
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # 4. Flip / update the display
    pygame.display.flip()

    # 5. Tick the clock (cap at FPS)
    clock.tick(FPS)

# ─────────────────────────────────────────
#  CLEAN UP
# ─────────────────────────────────────────
pygame.quit()
sys.exit()