import pygame
from settings import *
from math import atan2, degrees


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)
        self.ground = True

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class Gun(pygame.sprite.Sprite):
    def __init__(self, player, groups, type):
        #player connection
        self.player = player
        self.distance = 140
        self.player_direction = pygame.Vector2(1,0)

        #sprite setup
        super().__init__(groups)
        self.type = type
        self.gun_surf = pygame.image.load(join("images", "gun", self.type + ".png"))
        self.image = self.gun_surf
        self.rect = self.image.get_frect(center = self.player.rect.center + self.player_direction * self.distance)
        self.axerect = self.rect.inflate(0, -32)

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        self.player_direction = (mouse_pos - player_pos).normalize() if (mouse_pos - player_pos) else (mouse_pos - player_pos)

    def rotate_gun(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
        if self.player_direction.x > 0:
            self.image = pygame.transform.rotozoom(self.gun_surf, angle, 1)
        else:
            self.image = pygame.transform.rotozoom(self.gun_surf, abs(angle), 1)
            self.image = pygame.transform.flip(self.image, False, True)

    def update_surface(self):
        keys = pygame.key.get_just_pressed()
        if self.type == "axe":
            self.gun_surf = pygame.image.load(join("images", "gun", "axe.png"))
        elif self.type == "gun":
            self.gun_surf = pygame.image.load(join("images", "gun", "gun.png"))
        elif self.type == "gun2":
            self.gun_surf = pygame.image.load(join("images", "gun", "gun2.png"))
        else:
            self.gun_surf = pygame.image.load(join("images", "gun", "gun3.png"))


    def update(self, dt):
        self.update_surface()
        self.get_direction()
        self.rotate_gun()
        self.rect.center = self.player.rect.center + self.player_direction * self.distance

class Bullet(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, lifetime, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = lifetime

        self.direction = direction
        self.speed = 1200

    def update(self, dt):
        self.rect.center += self.speed * self.direction * dt

        if pygame.time.get_ticks() - self.spawn_time >= self.lifetime:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, enemy, round, collision_sprites):
        super().__init__(groups)
        self.player = player

        #image
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.animation_speed = 6

        #rect
        self.rect = self.image.get_frect(center = pos)
        self.hitbox_rect = self.rect.inflate(-20,-40)
        self.collision_sprites = collision_sprites
        self.direction = pygame.Vector2()

        #timer
        self.death_time = 0
        self.death_duration = 400

        #damage
        self.enemy = enemy
        self.round = round
        self.bullet_hurt = ""
        self.hit_time = 0

        #knockback
        self.knockback = 0
        self.knocked = False
        self.knockback_direction = pygame.Vector2()
        self.calc = (2 + (round/10)) if round > 1 else (1 + (round/10))

        if (self.enemy == "skeleton"):
            self.health = 60 * self.calc
            self.maxhealth = 60 * self.calc
            self.damage = 0.5 * self.calc
            self.speed = 350
        elif (self.enemy == "black"):
            self.health = 100 * self.calc
            self.maxhealth = 100 * self.calc
            self.damage = 0.9 * self.calc
            self.speed = 275
        elif (self.enemy == "skeletonbrute"):
            self.health = 100 * self.calc
            self.maxhealth = 100 * self.calc
            self.damage = 0.9 * self.calc
            self.speed = 275
        elif (self.enemy == "blackbrute"):
            self.health = 150 * self.calc
            self.maxhealth = 150 * self.calc
            self.damage = 1.3 * self.calc
            self.speed = 225
        elif (self.enemy == "skeletonice"):
            self.health = 50 * self.calc
            self.maxhealth = 50 * self.calc
            self.damage = 0.6 * self.calc
            self.speed = 400
        elif (self.enemy == "blackice"):
            self.health = 80 * self.calc
            self.maxhealth = 80 * self.calc
            self.damage = 1.0 * self.calc
            self.speed = 300
        elif (self.enemy == "skeletonfire"):
            self.health = 130 * self.calc
            self.maxhealth = 130 * self.calc
            self.damage = 1.1 * self.calc
            self.speed = 250
        elif (self.enemy == "blackfire"):
            self.health = 200 * self.calc
            self.maxhealth = 200 * self.calc
            self.damage = 1.6 * self.calc
            self.speed = 175
        elif (self.enemy == "skeletonspirit"):
            self.health = 40 * self.calc
            self.maxhealth = 40 * self.calc
            self.damage = 0.9 * self.calc
            self.speed = 450
        else:
            self.health = 70 * self.calc
            self.maxhealth = 70 * self.calc
            self.damage = 1.3 * self.calc
            self.speed = 350

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def move(self, dt):
        if self.knocked:
            if pygame.time.get_ticks() >= self.knockbackends:
                self.knocked = False
            else:
                self.hitbox_rect.x += self.knockback_direction.x * self.knockback * dt
                self.collisions("horizontal")
                self.hitbox_rect.y += self.knockback_direction.y * self.knockback * dt
                self.collisions("vertical")
                self.rect.center = self.hitbox_rect.center
        else:
            #get direction
            player_pos = pygame.Vector2(self.player.rect.center)
            enemy_pos = pygame.Vector2(self.rect.center)
            self.direction = (player_pos - enemy_pos).normalize() if (player_pos - enemy_pos) else (player_pos - enemy_pos)

            #update th rect position + collision
            self.hitbox_rect.x += self.direction.x * self.speed * dt
            self.collisions("horizontal")
            self.hitbox_rect.y += self.direction.y * self.speed * dt
            self.collisions("vertical")
            self.rect.center = self.hitbox_rect.center

    def collisions(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top

    def destroy(self):
        #start timer
        self.death_time = pygame.time.get_ticks()
        #change image
        surf = pygame.mask.from_surface(self.frames[0]).to_surface()
        surf.set_colorkey("black")
        self.image = surf

    def death_timer(self):
        if pygame.time.get_ticks() - self.death_time >= self.death_duration:
            self.kill()

    def applyknockback(self, direction, knockback):
        self.knocked = True
        self.knockback = knockback
        self.knockback_direction = direction
        self.knockbackstart = pygame.time.get_ticks()
        self.knockbackends = self.knockbackstart + 200

    def update(self, dt):
        if self.death_time == 0:
            self.move(dt)
            self.animate(dt)
        else:
            self.death_timer()

class Health(pygame.sprite.Sprite):
    def __init__(self, parent, groups , images):
        super().__init__(groups)
        self.levels = images
        self.image = self.levels[0]
        self.parent = parent
        self.rect = self.image.get_frect(midbottom = (self.parent.rect.centerx, self.parent.rect.centery - 40))

        self.health = self.parent.health
        self.maxhealth = self.parent.maxhealth
        self.healthlevel = 0

    def update(self, _):
        self.health = self.parent.health
        self.maxhealth = self.parent.maxhealth
        if self.health <= 0:
            self.kill()
        self.healthlevel = min(10, (10 - (int(self.health/self.maxhealth * 10))))
        self.image = self.levels[self.healthlevel]
        self.rect.midbottom = (self.parent.rect.centerx, self.parent.rect.centery - 40)

class Upgrade(pygame.sprite.Sprite):
    def __init__(self, pos, image, type, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_frect(center = pos)
        self.type = type



