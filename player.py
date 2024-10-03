import pygame.key
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        self.load_images()
        self.state, self.frame_index = "down", 0
        self.image = pygame.image.load(join("images", "player", "down", "0.png")).convert_alpha()
        self.rect = self.image.get_frect(center = pos)
        self.hitbox_rect = self.rect.inflate(-90, -90)
        
        #movement
        self.direction = pygame.math.Vector2()
        self.speed = 500
        self.collision_sprites = collision_sprites

        #health
        self.maxhealth = 100
        self.health = 100

        #upgrades
        self.axedmg = 10
        self.gundmg = 20
        self.lifesteal = 0
        self.knockback = 200

        #dash
        self.is_dashing = False
        self.dash_start = 0
        self.dash_length = 200
        self.dash_cooldown = 1000
        self.dashspeed = 3

    def load_images(self):
        self.frames = {"left": [], "right": [], "up": [], "down": []}
        for state in self.frames.keys():
            for folder_path, sub_folders, file_names in walk(join("images", "player", state)):
                if file_names:
                    for file_name in sorted(file_names, key = lambda name: int(name.split(".")[0])):
                        full_path = join(folder_path, file_name)
                        surf = pygame.image.load(full_path).convert_alpha()
                        self.frames[state].append(surf)

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

        if keys[pygame.K_q] and not self.is_dashing and pygame.time.get_ticks() - self.dash_start >= self.dash_cooldown:
            self.dash_start = pygame.time.get_ticks()
            self.is_dashing = True


    def move(self, dt):
        if self.is_dashing:
            speed = self.speed * 3
            if pygame.time.get_ticks() - self.dash_start >= self.dash_length:
                self.is_dashing = False
        else:
            speed = self.speed

        self.hitbox_rect.x += self.direction.x * speed * dt
        self.collision("horizontal")
        self.hitbox_rect.y += self.direction.y * speed * dt
        self.collision("vertical")
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top

                self.rect.center = self.hitbox_rect.center

    def animate(self, dt):
        #get state
        if self.direction.x != 0:
            self.state = "right" if self.direction.x > 0 else "left"
        if self.direction.y != 0:
            self.state = "down" if self.direction.y > 0 else "up"


        #animate
        self.frame_index = self.frame_index + 5 * dt if self.direction else 0
        self.image = self.frames[self.state][int(self.frame_index) % len(self.frames[self.state])]

    def update(self, dt):
        self.input()
        self.move(dt)
        self.animate(dt)

  

