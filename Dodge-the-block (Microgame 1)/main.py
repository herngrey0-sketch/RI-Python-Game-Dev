import os
import sys
import random

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
#  FONT & COLOURS  (R, G, B)
# ─────────────────────────────────────────
BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
RED    = (255,   0,   0)
YELLOW = (255,   255,   0)
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

game_over = False
score = 0
score_start_time = pygame.time.get_ticks()

# ─────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────
def draw_grid():
    """Draw a simple grid (optional visual)"""
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

def draw_scene():
    """Render one frame to the screen (without flipping)."""
    screen.fill(BLACK)
    draw_grid()
    pygame.draw.rect(screen, WHITE, player)
    pygame.draw.rect(screen, RED,   enemy)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

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
        player.y -= PLAYER_SPEED          # NOTE: UP decreases y in pygame
    if keys[pygame.K_DOWN]:
        player.y += PLAYER_SPEED

    # Movement “Pop” (Scale Up Slightly)
    if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]:
        player.width = 44
        player.height = 44
    else:
        player.width = 40
        player.height = 40

    # 2. Keep player inside the window
    player.clamp_ip(screen.get_rect())

    # 3. Move enemy left; wrap around when off-screen
    # enemy.x -= ENEMY_SPEED
    # if enemy.right < 0:
    #     enemy.x = SCREEN_WIDTH
    
    # Random respawn
    enemy.x -= 4
    if enemy.x < -40:
        enemy.x = 640
        enemy.y = random.randint(0, 440)

    # Detect collision
    if player.colliderect(enemy):
        # Screen flash before reset
        screen.fill(RED)
        pygame.display.flip()
        pygame.time.delay(100)

        # Player "pop" effect
        # player.inflate_ip(20, 20)
        # draw_scene()                # rerender the modified player
        # pygame.display.flip()
        # pygame.time.delay(50)
        # player.inflate_ip(-20, -20)
        
        # Color Flash, change player color for a moment
        # hit_color = RED
        # pygame.draw.rect(screen, hit_color, player)
        # pygame.display.flip()
        # pygame.time.delay(600)

        game_over = True

    # Reset game on loss
    if game_over:
        player.x, player.y = 100, 100
        enemy.x, enemy.y = 300, 200
        score = 0
        score_start_time = pygame.time.get_ticks()
        game_over = False
    
    # Increase score after every frame
    # score += 1
    
    # Increase score based on timer
    score = (pygame.time.get_ticks() - score_start_time) // 100

    # ── RENDER ───────────────────────────
    draw_scene()

    # Flip / update the display
    pygame.display.flip()

    # Tick the clock (cap at FPS)
    clock.tick(FPS)

# ─────────────────────────────────────────
#  CLEAN UP
# ─────────────────────────────────────────
pygame.quit()
sys.exit()