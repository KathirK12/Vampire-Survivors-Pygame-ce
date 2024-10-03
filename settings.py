import pygame 
from os.path import join 
from os import walk

WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720 
TILE_SIZE = 64

UPGRADE_DESCS = ["Gun Cooldown: Gun shoots faster", "Axe Damage Up: Increases axe damage", "Gun damage Up: Increases gun damage", "Max Health Up: Increases max health", "Dash Cooldown: Reduces dash cooldown", "Immunity Time Up: Increases time immune after a hit", "Piercing Up: Gives piercing, and extends length of piercing if taken more than once", "Knockback Up: Increases knockback distance", "Speed Up: Increases Speed", "Axe Cooldown: Increases axe speed", "Lifesteal Up: Increases health given back after killing a skeleton", "Normal Gun: Normal gun with average speed and damage", "Fast gun: Gun with amazing speed and low damage", "Strong Gun: Gun with great damage and low speed"]