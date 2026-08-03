import os
import sys
import random

# ── ENVIRONMENT SETUP ────────────────────────────────────────────────────────
# Set a virtual display if none exists (required for headless/Codespaces environments)
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"

# Suppress the "XDG_RUNTIME_DIR is invalid" warning by pointing to a temp folder
if not os.environ.get("XDG_RUNTIME_DIR"):
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-vscode"
    os.makedirs("/tmp/runtime-vscode", exist_ok=True)

# Use a dummy audio driver so pygame doesn't crash looking for sound hardware
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

# ── INITIALISE PYGAME ────────────────────────────────────────────────────────
# Must be called before using any pygame features
pygame.init()

# ── SCREEN SETTINGS ──────────────────────────────────────────────────────────
# Define the window dimensions and title
SCREEN_WIDTH  = 640
SCREEN_HEIGHT = 480
TITLE         = "Pygame"

# Create the game window with the specified size
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)

# ── GAME STATE ───────────────────────────────────────────────────────────────
# Tracks which screen is currently active: "menu" or "gameplay"
state = "menu"

# ── CLOCK & FPS ──────────────────────────────────────────────────────────────
# Clock is used to cap the game loop at a consistent frame rate
clock = pygame.time.Clock()
FPS = 60

spawn_timer = 0
spawn_interval = 60

# ── COLOURS ──────────────────────────────────────────────────────────────────
# Reusable RGB colour constants used throughout rendering
BLACK  = (  0,   0,   0)
WHITE  = (255, 255, 255)
RED    = (255,   0,   0)
GREEN  = (  0, 255,   0)
GRAY   = ( 40,  40,  40)   # Used for the background grid lines

# ── FONT ─────────────────────────────────────────────────────────────────────
# Default pygame font at size 36, used for score and menu text
font = pygame.font.Font(None, 36)

# ── PLAYER ───────────────────────────────────────────────────────────────────
# White square the user controls with arrow keys
player = pygame.Rect(100, 100, 40, 40)
PLAYER_SPEED = 5             # Pixels moved per frame

# ── ENEMY ────────────────────────────────────────────────────────────────────
# Red square enemy (currently disabled/commented out in logic)
enemy = pygame.Rect(300, 200, 40, 40)
ENEMY_SPEED = 3

# ── ENEMIES ──────────────────────────────────────────────────────────────────
# Moving red squares that reset the player and score on contact
enemies = [
    pygame.Rect(400, 150, 30, 30),
]

# ── SCORE ────────────────────────────────────────────────────────────────────
score = 0

# ── GRID HELPER ──────────────────────────────────────────────────────────────
# Draws a subtle background grid to give the arena some visual structure
def draw_grid():
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

# ── GAME LOOP FLAGS ──────────────────────────────────────────────────────────
# running: controls whether the main loop continues
# game_over: signals that the player hit a enemy this frame
running = True
game_over = False

# ── MAIN GAME LOOP ───────────────────────────────────────────────────────────
# Runs every frame until the user quits
while running:

    # ── EVENT HANDLING ───────────────────────────────────────────────────────
    # Process all events queued since the last frame
    for event in pygame.event.get():

        # Clicking the window's X button stops the loop
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Escape key quits the game from any state
            if event.key == pygame.K_ESCAPE:
                running = False

            # Space bar on the menu transitions to gameplay
            if state == "menu" and event.key == pygame.K_SPACE:
                state = "gameplay"
            
            if state == "gameover" and event.key == pygame.K_r:
                state = "menu"

    # ── GAMEPLAY UPDATE ──────────────────────────────────────────────────────
    # All game logic is skipped while on the menu screen
    if state == "gameplay":

        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            enemies.append(pygame.Rect(random.randint(0, 600), random.randint(0, 400), 30, 30))

        if spawn_interval > 15:
            spawn_interval -= 0.005
            
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
        # If the player touches a enemy, flag game_over for handling below
        for e in enemies:
            if player.colliderect(e):
                player.x, player.y = 100, 200
                state = "gameover"
                game_over = True
        
        # Increase score every frame
        score += 1

        # ── GAME OVER HANDLING ───────────────────────────────────────────────
        # Briefly flash red, then reset all game objects back to their starting state
        if game_over:
            screen.fill(RED)
            pygame.display.flip()
            pygame.time.delay(100)      # Hold the red screen for 100 ms

            # Reset player position, score
            player.x, player.y = 300, 200
            score = 0
            spawn_timer = 0
            spawn_interval = 60
            enemies = [
                pygame.Rect(400, 150, 30, 30),
            ]
            game_over = False           # Clear the flag so we don't loop here again

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

    # ── RENDER: GAMEPLAY ─────────────────────────────────────────────────────
    # Draw all game objects and the HUD each frame during gameplay
    elif state == "gameplay":
        screen.fill(BLACK)              # Clear the previous frame

        draw_grid()                     # Subtle background grid

        pygame.draw.rect(screen, WHITE, player)     # Player square

        # Draw all enemies as red squares
        for e in enemies:
            pygame.draw.rect(screen, RED, e)

        # Display the current score in the top-left corner
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # Push the drawn frame to the display and cap the loop speed
        pygame.display.flip()
        clock.tick(FPS)
    
    elif state == "gameover":
        screen.fill((80, 0, 0))
        over_text = font.render("GAME OVER", True, WHITE)
        restart_text =  font.render("Press R to restart", True, (200, 200, 200))
        screen.blit(over_text, (250, 150))
        screen.blit(restart_text, (220, 220))
        pygame.display.flip()
        clock.tick(FPS)

# ── CLEANUP ──────────────────────────────────────────────────────────────────
# Shut down pygame properly and exit the Python process
pygame.quit()
sys.exit()