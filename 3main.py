import pygame
import random


def screen_shake(intensity = 5, duration = 10):
    offsets = []
    for _ in range(duration):
        ox = random.randint(-intensity, +intensity)
        oy = random.randint(-intensity, +intensity)
        offsets.append((ox, oy))
    return offsets


def hit_flash(surface, color = (255, 0, 0), duration = 60):
    surface.fill(color)
    pygame.display.flip()
    pygame.time.delay(duration)


def pop_effect(surface, rect, color, amount=4, duration=40):
    rect.inflate_ip(amount, amount)
    pygame.draw.rect(surface, color, rect)
    pygame.display.flip()
    pygame.time.delay(duration)
    rect.inflate_ip(-amount, -amount)


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


# ─────────────────────────────────────────
#  GAME OBJECTS
# ─────────────────────────────────────────
player = pygame.Rect(300, 200, 40, 40)
PLAYER_SPEED = 5             # Pixels moved per frame


enemies = [
    pygame.Rect(100, 100, 30, 30),
]


# ─────────────────────────────────────────
#  VARIABLES
# ─────────────────────────────────────────
shake_offsets = []
pending_gameover = False


font = pygame.font.Font(None, 36)


# Tracks which screen is currently active
state = "menu"


spawn_timer = 0
spawn_interval = 60 # frame interval (Default is 60FPS so about 1 second)


score = 0


# ─────────────────────────────────────────
#  HELPER: draw a simple grid (optional visual)
# ─────────────────────────────────────────
def draw_grid(surface):
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(surface, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(surface, GRAY, (0, y), (SCREEN_WIDTH, y))


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


            # R key on the gameover screen transitions back to menu
            if state == "gameover" and event.key == pygame.K_r:
                # Reset all game objects back to their starting state
                pending_gameover = False
                player.x, player.y = 300, 200
                spawn_timer = 0
                spawn_interval = 60
                enemies = [
                    pygame.Rect(400, 150, 30, 30),
                ]
                state = "menu"


    # ── UPDATE: GAMEPLAY ───────────────────
    if state == "gameplay" and not pending_gameover:
        # ── PLAYER MOVEMENT ──────────────────────────────────────────────────
        # Read which arrow keys are currently held and move the player accordingly
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            player.x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            player.y -= PLAYER_SPEED    # In pygame, y decreases going up
        if keys[pygame.K_DOWN]:
            player.y += PLAYER_SPEED


        # ── BOUNDARY CLAMPING ────────────────────────────────────────────────
        # Prevent the player from moving outside the window edges
        player.clamp_ip(screen.get_rect())
       
        # ── ENEMY MOVEMENT ──────────────────────────────────────────────────
        # Each enemy tracks player
        for e in enemies:
            if e.x < player.x: e.x += 2
            if e.x > player.x: e.x -= 2
            if e.y < player.y: e.y += 2
            if e.y > player.y: e.y -= 2


        # ── ENEMY COLLISION ─────────────────────────────────────────────────
        # If the player touches a enemy, game over
        for e in enemies:
            if player.colliderect(e):
                if not pending_gameover:          
                    shake_offsets = screen_shake()
                    pending_gameover = True


        score += 1


        # ── SPAWNING ENEMY ───────────────────────────────────────────────
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            enemies.append(pygame.Rect(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), 30, 30))
       
        if spawn_interval > 15:
            spawn_interval -= 0.005


    # ── RENDER: MENU ─────────────────────────────────────────────────────────
    # Draw the title screen with instructions when in menu state
    if state == "menu":
        screen.fill(BLACK)


        # Render and position the game title and start prompt
        title_text = font.render("SURVIVE THE ARENA", True, WHITE)
        start_text = font.render("Press SPACE to start", True, (200, 200, 200))
        screen.blit(title_text, (150, 150))
        screen.blit(start_text, (160, 220))


        # Push the drawn frame to the display and cap the loop speed
        pygame.display.flip()
        clock.tick(FPS)


    # ── RENDER: GAMEPLAY ───────────────────────────
    elif state == "gameplay":
        game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        game_surface.fill(BLACK)
        draw_grid(game_surface)


        # Draw the Player square
        pygame.draw.rect(game_surface, WHITE, player)


        # Draw the Enemy square
        for e in enemies:
            pygame.draw.rect(game_surface, RED, e)


        # Display the current score in the top-left corner
        score_text = font.render(f"Score: {score}", True, WHITE)
        game_surface.blit(score_text, (10, 10))


        # Pop the next offset, or use (0,0) when the list is exhausted
        ox, oy = shake_offsets.pop(0) if shake_offsets else (0, 0)
        screen.blit(game_surface, (ox, oy))


        if pending_gameover and not shake_offsets:
            state = "gameover"
            pending_gameover = False


        # Flip / update the display
        pygame.display.flip()


        # Tick the clock (cap at FPS)
        clock.tick(FPS)


    elif state == "gameover":
        screen.fill((80, 0, 0))
        over_text = font.render("GAME OVER", True, WHITE)
        restart_text =  font.render("Press R to restart", True, (200, 200, 200))
        screen.blit(over_text, (250, 150))
        screen.blit(restart_text, (220, 220))
        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────
#  CLEAN UP
# ─────────────────────────────────────────
pygame.quit()
sys.exit()

