import os
import sys


# Headless / Codespaces environment fixes
if not os.environ.get("DISPLAY"):
	os.environ["DISPLAY"] = ":99"

if not os.environ.get("XDG_RUNTIME_DIR"):
	os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-vscode"
	os.makedirs("/tmp/runtime-vscode", exist_ok=True)

os.environ["SDL_AUDIODRIVER"] = "dummy"


import pygame 
import random


# Initialise pygame
pygame.init()


# Screen / window setup
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
TITLE = "Reckless Driving Simulator"
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)


# Clock
clock = pygame.time.Clock()
FPS = 60


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
YELLOW = (255, 220, 0)
BLUE = (40, 130, 255)
RED = (240, 55, 45)
ORANGE = (255, 125, 25)


# Game objects
PLAYER_SIZE = 40
PLAYER_BASE_Y = 390
LANE_CENTERS = (150, 320, 490)
PLAYER_SPEED = 12
player = pygame.Rect(0, PLAYER_BASE_Y, PLAYER_SIZE, PLAYER_SIZE)
player.centerx = LANE_CENTERS[1]
target_lane = 1
jump_duration = 48
jump_timer = 0

BLOCK_SIZE = 40
blocks = []
coins = []
coin_spawn_timer = 0
block_spawn_timer = 0
last_block_lane = -1
survival_frames = 0
score = 0
high_score = 91

# Game state and display
state = "menu"
flash_timer = 0
new_high_score = False
font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 24)
title_font = pygame.font.Font(None, 48)


def draw_grid(surface):
	for x in range(0, SCREEN_WIDTH, 40):
		pygame.draw.line(surface, GRAY, (x, 0), (x, SCREEN_HEIGHT))
	for y in range(0, SCREEN_HEIGHT, 40):
		pygame.draw.line(surface, GRAY, (0, y), (SCREEN_WIDTH, y))

	for lane_x in LANE_CENTERS:
		pygame.draw.line(surface, (70, 70, 70), (lane_x, 0), (lane_x, SCREEN_HEIGHT), 2)


def reset_game():
	global target_lane, jump_timer, blocks, coins, coin_spawn_timer
	global block_spawn_timer, last_block_lane, survival_frames, score
	global new_high_score, flash_timer

	target_lane = 1
	player.centerx = LANE_CENTERS[target_lane]
	player.y = PLAYER_BASE_Y
	jump_timer = 0
	blocks = []
	coins = []
	coin_spawn_timer = 0
	block_spawn_timer = 35
	last_block_lane = -1
	survival_frames = 0
	score = 0
	new_high_score = False
	flash_timer = 0
	spawn_coin()


def spawn_coin():
	available_lanes = [lane for lane in range(len(LANE_CENTERS))
					   if abs(LANE_CENTERS[lane] - player.centerx) > PLAYER_SIZE]
	if not available_lanes:
		available_lanes = list(range(len(LANE_CENTERS)))
	lane = random.choice(available_lanes)
	coins.append({"x": LANE_CENTERS[lane], "y": -12})


def spawn_block():
	global last_block_lane

	lanes = [lane for lane in range(len(LANE_CENTERS)) if lane != last_block_lane]
	lane = random.choice(lanes or list(range(len(LANE_CENTERS))))
	last_block_lane = lane
	block = pygame.Rect(0, -BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
	block.centerx = LANE_CENTERS[lane]
	color = random.choice((ORANGE, RED))
	blocks.append({
		"rect": block,
		"color": color,
		"target_x": block.centerx,
		"swerve_timer": random.randint(18, 42),
		"swerve_speed": random.randint(7, 12),
	})


def draw_centered_text(surface, text, text_font, color, y):
	rendered = text_font.render(text, True, color)
	surface.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2, y))


def finish_game():
	global state, high_score, new_high_score, flash_timer

	new_high_score = score > high_score
	if new_high_score:
		high_score = score
	flash_timer = 10
	state = "hit_flash"


reset_game()
running = True


while running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				running = False
			elif state == "menu" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
				reset_game()
				state = "gameplay"
			elif state == "gameover":
				if event.key == pygame.K_r:
					reset_game()
					state = "gameplay"
				elif event.key == pygame.K_m:
					state = "menu"
			elif state == "gameplay":
				if event.key in (pygame.K_LEFT, pygame.K_a):
					target_lane = max(0, target_lane - 1)
				elif event.key in (pygame.K_RIGHT, pygame.K_d):
					target_lane = min(len(LANE_CENTERS) - 1, target_lane + 1)
				elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE) and jump_timer == 0:
					jump_timer = jump_duration

	if state == "gameplay":
		survival_frames += 1

		target_x = LANE_CENTERS[target_lane]
		if player.centerx < target_x:
			player.centerx = min(target_x, player.centerx + PLAYER_SPEED)
		elif player.centerx > target_x:
			player.centerx = max(target_x, player.centerx - PLAYER_SPEED)

		jump_height = 0
		if jump_timer > 0:
			progress = 1 - jump_timer / jump_duration
			jump_height = int(100 * (4 * progress * (1 - progress)))
			jump_timer -= 1

		difficulty = min(score, 100)
		block_speed = min(8.0, 4.0 + difficulty * 0.04)
		spawn_interval = max(42, 78 - difficulty // 4 * 2)
		block_spawn_timer += 1
		if block_spawn_timer >= spawn_interval:
			block_spawn_timer = 0
			spawn_block()

		for block in blocks[:]:
			if block["color"] == RED:
				block["swerve_timer"] -= 1
				if block["swerve_timer"] <= 0:
					current_lane = min(
						range(len(LANE_CENTERS)),
						key=lambda lane: abs(LANE_CENTERS[lane] - block["rect"].centerx),
					)
					other_lanes = [
						lane_x for lane_x in LANE_CENTERS
						if lane_x != LANE_CENTERS[current_lane]
					]
					block["target_x"] = random.choice(other_lanes)
					block["swerve_timer"] = random.randint(18, 42)

				if block["rect"].centerx < block["target_x"]:
					block["rect"].centerx = min(
						block["target_x"],
						block["rect"].centerx + block["swerve_speed"],
					)
				elif block["rect"].centerx > block["target_x"]:
					block["rect"].centerx = max(
						block["target_x"],
						block["rect"].centerx - block["swerve_speed"],
					)
			block["rect"].y += block_speed
			if block["rect"].top > SCREEN_HEIGHT:
				blocks.remove(block)
			elif jump_height < 50 and block["rect"].colliderect(player):
				finish_game()
				break

		if state == "gameplay":
			coin_spawn_timer += 1
			if coin_spawn_timer >= 90 and len(coins) < 3:
				coin_spawn_timer = 0
				spawn_coin()

			visible_player = player.copy()
			visible_player.y -= jump_height
			for coin in coins[:]:
				coin["y"] += block_speed
				if coin["y"] - 12 > SCREEN_HEIGHT:
					coins.remove(coin)
					continue
				coin_rect = pygame.Rect(coin["x"] - 12, coin["y"] - 12, 24, 24)
				if visible_player.colliderect(coin_rect):
					coins.remove(coin)
					score += 1

	elif state == "hit_flash":
		flash_timer -= 1
		if flash_timer <= 0:
			state = "gameover"

	screen.fill(BLACK)
	draw_grid(screen)

	if state == "menu":
		draw_centered_text(screen, "RECKLESS DRIVING SIMULATOR", title_font, WHITE, 125)
		draw_centered_text(screen, "Blue: Player", small_font, BLUE, 205)
		draw_centered_text(screen, "Orange: Normal Car (drives normally)", small_font, ORANGE, 231)
		draw_centered_text(screen, "Red: Reckless Car (randomly move around)", small_font, RED, 257)
		draw_centered_text(screen, "Yellow Coins: Coins (gives points) [bicycles]", small_font, YELLOW, 283)
		draw_centered_text(screen, "A / D to move left / right; SPACE to jump", small_font, WHITE, 330)
		draw_centered_text(screen, "SPACE to start", font, YELLOW, 365)
		draw_centered_text(screen, f"High Score: {high_score}", small_font, YELLOW, 420)
	else:
		for coin in coins:
			pygame.draw.circle(screen, YELLOW, (coin["x"], coin["y"]), 12)
			pygame.draw.circle(screen, WHITE, (coin["x"], coin["y"]), 12, 2)

		for block in blocks:
			pygame.draw.rect(screen, block["color"], block["rect"])

		player_draw = player.copy()
		if state == "gameplay" and jump_timer > 0:
			progress = 1 - jump_timer / jump_duration
			player_draw.y -= int(100 * (4 * progress * (1 - progress)))
		pygame.draw.rect(screen, BLUE, player_draw)
		pygame.draw.rect(screen, WHITE, player_draw, 2)

		score_text = font.render(f"Score: {score}", True, WHITE)
		high_text = small_font.render(f"Best: {high_score}", True, YELLOW)
		screen.blit(score_text, (18, 16))
		screen.blit(high_text, (SCREEN_WIDTH - high_text.get_width() - 18, 22))

		if state == "hit_flash":
			flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
			flash_surface.fill(RED)
			flash_surface.set_alpha(150)
			screen.blit(flash_surface, (0, 0))
		elif state == "gameover":
			overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
			overlay.fill(BLACK)
			overlay.set_alpha(190)
			screen.blit(overlay, (0, 0))
			draw_centered_text(screen, "You Lose!", title_font, RED, 125)
			draw_centered_text(screen, f"Score: {score}", font, WHITE, 205)
			if new_high_score:
				draw_centered_text(screen, f"You beat your High Score. New Score: {score}", small_font, YELLOW, 255)
			draw_centered_text(screen, "R to play again", small_font, WHITE, 330)

	pygame.display.flip()
	clock.tick(FPS)


# Clean up
pygame.quit()
sys.exit()
