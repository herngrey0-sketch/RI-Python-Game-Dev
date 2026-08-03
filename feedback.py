import pygame
import random

def screen_shake(intensity = 5, duration = 10):
    offsets = [ ]
    for _ in range(duration):
        ox = random.randint(-intensity, +intensity)
        oy = random.randint(-intensity, +intensity)
        offsets.append((ox, oy))
    return offsets

