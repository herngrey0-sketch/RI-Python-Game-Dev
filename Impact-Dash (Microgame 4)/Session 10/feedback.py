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