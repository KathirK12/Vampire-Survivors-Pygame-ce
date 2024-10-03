import pygame
from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites

from random import randint, choice

class Game:
    def __init__(self):
        #setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Survivor")
        self.clock = pygame.time.Clock()
        self.running = True

        #groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.healthbars = pygame.sprite.Group()
        self.upgrades = pygame.sprite.Group()

        #gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 300
        self.bullet_shot = ""

        #enemy timer
        self.enemys = 0
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 500)
        self.spawn_positions = []

        #audio
        self.shoot_sound = pygame.mixer.Sound(join("audio", "shoot.wav"))
        self.shoot_sound.set_volume(0.4)
        self.impact_sound = pygame.mixer.Sound(join("audio", "impact.ogg"))
        self.music = pygame.mixer.Sound(join("audio", "music.wav"))
        self.music.set_volume(0.3)
        self.music.play(loops=-1)

        #damage
        self.hurt_time = 0
        self.immunity_time = 700
        self.axe_immunity = 300
        self.piercing = False
        self.axe_sound = 0
        self.gun_sound = 0
        self.bullet_sound = 0
        self.lifetime = 1000

        #upgrade
        self.kills = 0
        self.upgrade_positions = []
        self.permgun = "gun"
        self.gunchosen = False
        self.upgrade_descs = UPGRADE_DESCS

        #rounds
        self.roundkills = 0
        self.round = 0
        self.roundrunning = True
        self.roundstart = pygame.time.get_ticks()
        self.font = pygame.font.Font(join("images", "font", "PixelifySans-Regular.ttf"), 24)
        self.time = pygame.font.Font(join("images", "font", "PixelifySans-Regular.ttf"), 48)
        self.score_event = pygame.event.custom_type()
        self.score_time = self.time.render("0", True, (255, 255, 255))
        self.roundtime = 0
        self.oldx = 1000
        self.textbox = pygame.image.load(join("images", "textbox.png")).convert_alpha()
        pygame.time.set_timer(self.score_event, 1000)

        #setup
        self.load_images()
        self.setup()

    def load_images(self):
        self.bullet_surf = pygame.image.load(join("images", "gun", "bullet.png")).convert_alpha()

        folders = list(walk(join("images", "enemies")))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join("images", "enemies", folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split(".")[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

        files = list(walk(join("images", "health")))[0][1]
        self.healthlevels = []
        self.playerhealthlevels = []
        self.upgradelevels = []
        for i in range(0, 11):
            surf = pygame.image.load(join("images", "health", str(i) + ".png")).convert_alpha()
            self.healthlevels.append(surf)
            surf = pygame.image.load(join("images", "playerhealth", str(i) + ".png")).convert_alpha()
            self.playerhealthlevels.append(surf)
            surf = pygame.image.load(join("images", "upgrades", str(i) + ".png")).convert_alpha()
            self.upgradelevels.append(surf)

        self.guns = []
        for i in range(0,3):
            if i == 0:
                self.guns.append(pygame.image.load(join("images", "gun", "gun.png")))
            elif i == 1:
                self.guns.append(pygame.image.load(join("images", "gun", "gun2.png")))
            else:
                self.guns.append(pygame.image.load(join("images", "gun", "gun3.png")))

        self.scorebox = pygame.image.load(join("images", "scorebox.png")).convert_alpha()

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot and self.gun.type != "axe":
            if pygame.time.get_ticks() - self.bullet_sound >= self.gun_cooldown if self.gun_cooldown > 40 else 40:
                self.impact_sound.play()
                self.bullet_sound = pygame.time.get_ticks()
            pos = self.gun.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, self.lifetime, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self, shoot_time):
        if not self.can_shoot:
            if pygame.time.get_ticks() - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def setup(self):
        map = load_pygame(join("data", "maps", "world.tmx"))
        for x, y, image in map.get_layer_by_name("Ground").tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.all_sprites))

        for obj in map.get_layer_by_name("Objects"):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name("Collisions"):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name("Entities"):
            if obj.name == "Player":
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                self.playerhealthlevel = min(10, (10 - (int(self.player.health / self.player.maxhealth * 10))))
                Health(self.player, self.all_sprites, self.healthlevels)
                self.gun = Gun(self.player, self.all_sprites, "axe")
            elif obj.name == "Enemy":
                self.spawn_positions.append((obj.x, obj.y))
            else:
                self.upgrade_positions.append((obj.x, obj.y))

        self.stats = []
        self.statrenders = []
        for i in range(0, 11):
            if i == 0:
                self.stats.append("Gun Speed: " + str(self.gun_cooldown))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 1:
                self.stats.append("Axe Damage: " + str(self.player.axedmg))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 2:
                self.stats.append("Gun Damage: " + str(self.player.gundmg))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 3:
                self.stats.append("Max Health: " + str(self.player.maxhealth))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 4:
                self.stats.append("Dash Cooldown: " + str(self.player.dash_cooldown))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 5:
                self.stats.append("Immunity Time: " + str(self.immunity_time))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 6:
                self.stats.append("Piercing: " + str(self.piercing))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 7:
                self.stats.append("Knockback:  " + str(self.player.knockback))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 9:
                self.stats.append("Axe Speed:  " + str(self.axe_immunity))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            elif i == 8:
                self.stats.append("Speed: " + str(self.player.speed))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))
            else:
                self.stats.append("Life Steal: " + str(self.player.lifesteal))
                self.statrenders.append(self.font.render(self.stats[i], True, (255, 255, 255)))

    def bullet_collision(self):
        if self.bullet_sprites and self.gun.type != "axe":
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    if pygame.time.get_ticks() - self.gun_sound >= self.gun_cooldown if self.gun_cooldown > 200 else 200 and self.bullet_shot != bullet:
                        self.bullet_shot = bullet
                        self.impact_sound.play()
                        self.gun_sound = pygame.time.get_ticks()
                    for sprite in collision_sprites:
                        if bullet != sprite.bullet_hurt:
                            sprite.bullet_hurt = bullet
                            sprite.health -= self.player.gundmg
                            direction = pygame.Vector2(sprite.rect.center) - pygame.Vector2(bullet.rect.center)
                            direction = direction.normalize() if pygame.Vector2(sprite.rect.center) - pygame.Vector2(bullet.rect.center) else pygame.Vector2(sprite.rect.center) - pygame.Vector2(bullet.rect.center)
                            sprite.applyknockback(direction, self.player.knockback)
                            if sprite.health <= 0:
                                sprite.destroy()
                                self.kills += 1
                                self.roundkills += 1
                                self.enemys -= 1
                                self.player.health += self.player.lifesteal
                                if self.player.health > self.player.maxhealth:
                                    self.player.health = self.player.maxhealth
                    if not self.piercing:
                        bullet.kill()
        else:
            if self.gun.type == "axe":
                collision_sprites = pygame.sprite.spritecollide(self.gun, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    if pygame.time.get_ticks() - self.axe_sound >= self.axe_immunity if self.axe_immunity > 40 else 40:
                        self.impact_sound.play()
                        self.axe_sound = pygame.time.get_ticks()
                    for sprite in collision_sprites:
                        if pygame.time.get_ticks() - sprite.hit_time >= self.axe_immunity:
                            sprite.hit_time = pygame.time.get_ticks()
                            sprite.health -= self.player.axedmg
                            direction = pygame.Vector2(sprite.rect.center) - pygame.Vector2(self.gun.rect.center)
                            direction = direction.normalize() if pygame.Vector2(sprite.rect.center) - pygame.Vector2(self.gun.rect.center) else pygame.Vector2(sprite.rect.center) - pygame.Vector2(self.gun.rect.center)
                            sprite.applyknockback(direction, self.player.knockback)
                            if sprite.health <= 0:
                                sprite.destroy()
                                self.kills += 1
                                self.roundkills += 1
                                self.enemys -= 1
                                self.player.health += self.player.lifesteal
                                if self.player.health > self.player.maxhealth:
                                    self.player.health = self.player.maxhealth

    def player_collision(self):
        enemy_collides = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask)
        if enemy_collides and pygame.time.get_ticks() - self.hurt_time >= self.immunity_time and not self.player.is_dashing:
            self.hurt_time = pygame.time.get_ticks()
            for enemy in enemy_collides:
                self.player.health -= enemy.damage
        if self.player.health <= 0:
            self.running = False

    def weapon_change(self):
        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_2] and self.gun.type != "axe":
            self.gun.type = "axe"
        if keys[pygame.K_1] and self.gun.type == "axe" and self.gunchosen:
            self.gun.type = self.permgun

    def progression(self):
        if self.kills >= 10:
            self.kills = 0
            upgrade = randint(0,4)
            if upgrade == 0:
                self.gun_cooldown -= 0.1
                if self.gun_cooldown <= 0:
                    self.gun_cooldown = 0
            elif upgrade == 1:
                self.player.axedmg += 0.1
            elif upgrade == 2:
                self.player.gundmg += 0.1
            elif upgrade == 3:
                self.player.maxhealth += 1
                self.player.health = self.player.maxhealth
            else:
                self.player.lifesteal += 0.1

    def checkround(self):
        if ((pygame.time.get_ticks() - self.roundstart >= self.round * 10000 and self.roundrunning) or self.roundkills > self.round * 20):
            for enemy in self.enemy_sprites:
                enemy.kill()
            for healthbar in self.healthbars:
                healthbar.kill()
            self.player.health = self.player.maxhealth
            self.roundrunning = False
            self.roundkills = 0
            r1 = randint(0, 10)
            r2 = randint(0, 10)
            r3 = randint(0, 10)
            if self.round != 0:
                Upgrade(self.upgrade_positions[0], self.upgradelevels[r1], r1, (self.all_sprites, self.upgrades))
                Upgrade(self.upgrade_positions[1], self.upgradelevels[r2], r2, (self.all_sprites, self.upgrades))
                Upgrade(self.upgrade_positions[2], self.upgradelevels[r3], r3, (self.all_sprites, self.upgrades))
            else:
                Upgrade(self.upgrade_positions[0], self.guns[1], 12, (self.all_sprites, self.upgrades))
                Upgrade(self.upgrade_positions[1], self.guns[0], 11, (self.all_sprites, self.upgrades))
                Upgrade(self.upgrade_positions[2], self.guns[2], 13, (self.all_sprites, self.upgrades))

    def upgradecheck(self):
        if not self.roundrunning:
            upgrades = pygame.sprite.spritecollide(self.player, self.upgrades, False, pygame.sprite.collide_mask)
            if upgrades:
                for upgrade in upgrades:
                    type = upgrade.type
                    if self.round != 0:
                        if type == 0:
                            self.gun_cooldown -= 50
                            if self.gun_cooldown < 0:
                                self.gun_cooldown = 0
                        elif type == 1:
                            self.player.axedmg += 15
                        elif type == 2:
                            self.player.gundmg += 10
                        elif type == 3:
                            self.player.maxhealth += 10
                            self.player.health = self.player.maxhealth
                        elif type == 4:
                            self.player.dash_cooldown -= 50
                            if self.player.dash_cooldown < 0:
                                self.player.dash_cooldown = 0
                        elif type == 5:
                            self.immunity_time += 75
                        elif type == 6:
                            if self.piercing:
                                if self.permgun == "gun1":
                                    if not self.lifetime >= 1500:
                                        self.lifetime += 100
                                elif self.permgun == "gun":
                                    if not self.lifetime >= 2000:
                                        self.lifetime += 100
                                else:
                                    if not self.lifetime >= 2500:
                                        self.lifetime += 100
                            else:
                                self.piercing = True
                        elif type == 7:
                            self.player.knockback += 10
                        elif type == 8:
                            self.player.speed += 10
                        elif type == 9:
                            self.axe_immunity -= 50
                            if self.axe_immunity < 0:
                                self.axe_immunity = 0
                        else:
                            self.player.lifesteal += 10
                        upgrade.kill()
                    else:
                        if type == 10:
                            self.gun.type = "gun"
                            self.permgun = "gun"
                            self.gunchosen = True
                            self.gun_cooldown = 400
                            self.player.gundmg = 10
                        elif type == 11:
                            self.gun.type = "gun2"
                            self.permgun = "gun2"
                            self.gunchosen = True
                            self.gun_cooldown = 300
                            self.player.gundmg = 3
                        else:
                            self.gun.type = "gun3"
                            self.permgun = "gun3"
                            self.gunchosen = True
                            self.gun_cooldown = 700
                            self.gundmg = 30

                for upgrade in self.upgrades:
                    upgrade.kill()
                self.round += 1
                self.roundrunning = True
                self.roundtime = 0
                self.roundstart = pygame.time.get_ticks()

    def updatestats(self):

        for i in range(0, 11):
            if i == 0:
                self.stats[i] = ("Gun Speed: " + str(int(self.gun_cooldown)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 1:
                self.stats[i] = ("Axe Damage: " + str(int(self.player.axedmg)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 2:
                self.stats[i] = ("Gun Damage: " + str(int(self.player.gundmg)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 3:
                self.stats[i] = ("Max Health: " + str(int(self.player.maxhealth)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 4:
                self.stats[i] = ("Dash Cooldown: " + str(int(self.player.dash_cooldown)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 5:
                self.stats[i] = ("Immunity Time: " + str(int(self.immunity_time)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 6:
                self.stats[i] = ("Piercing: " + str(int(self.piercing)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 7:
                self.stats[i] = ("Knockback:  " + str(int(self.player.knockback)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 9:
                self.stats[i] = ("Axe Speed:  " + str(int(self.axe_immunity)))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            elif i == 8:
                self.stats[i] = "Speed: " + str(int(self.player.speed))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))
            else:
                self.stats[i] = "Life Steal: " + str(int(self.player.lifesteal))
                self.statrenders[i] = (self.font.render(self.stats[i], True, (213,174,44)))

    def upgradehover(self):
        if not self.roundrunning:
            mouse = pygame.mouse.get_pos()
            for upgrade in self.upgrades:
                surf = pygame.Surface((128,128))
                randrect = surf.get_frect(center=(upgrade.rect.centerx - (self.player.rect.center[0] - WINDOW_WIDTH / 2), upgrade.rect.center[1] - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
                if randrect.collidepoint(mouse):
                    rendered_text = self.font.render(self.upgrade_descs[upgrade.type], True, (255,255,255), bgcolor=(0,0,0), wraplength=300)
                    self.display_surface.blit(rendered_text, (upgrade.rect.topright[0] - (self.player.rect.centerx - WINDOW_WIDTH / 2),upgrade.rect.topright[1] - (self.player.rect.centery - WINDOW_HEIGHT / 2)))

    def checkcursor(self):
        if pygame.mouse.get_pos()[0] < 40:
            if self.player.rect.centerx - self.oldx  <= self.player.rect.centerx - 630:
                if self.player.rect.centerx - (self.oldx - 50) != self.player.rect.centerx - 600:
                    self.display_surface.blit(self.textbox, (self.player.rect.centerx - (self.oldx + 30) - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - 240 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
                else:
                    self.display_surface.blit(self.textbox, (self.player.rect.centerx - 630 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - 240 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
            for i in range(0,11):
                if self.player.rect.centerx - (self.oldx - 50) <= self.player.rect.centerx - 600:
                    yoffset = 200 - (i * 40)
                    if self.player.rect.centerx - (self.oldx - 50) != self.player.rect.centerx - 600:
                        self.display_surface.blit(self.statrenders[i], (self.player.rect.centerx - (self.oldx - 50) - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - yoffset - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
                        self.oldx = self.oldx - 50
                    else:
                        self.display_surface.blit(self.statrenders[i], (self.player.rect.centerx - 600 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - yoffset - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
        else:
            if self.player.rect.centerx - (self.oldx + 50) > self.player.rect.centerx - 1000:
                if self.player.rect.centerx - self.oldx != self.player.rect.centerx - 1000:
                    self.display_surface.blit(self.textbox, (self.player.rect.centerx - self.oldx - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - 240 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
                else:
                    self.display_surface.blit(self.textbox, (self.player.rect.centerx - 1000 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - 240 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
            for i in range(0, 11):
                if self.player.rect.centerx - (self.oldx + 50) > self.player.rect.centerx - 1000:
                    yoffset = 300 - (i * 40)
                    if self.player.rect.centerx - (self.oldx + 50) != self.player.rect.centerx - 1000:
                        self.display_surface.blit(self.statrenders[i], (self.player.rect.centerx - (self.oldx + 50) - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - yoffset - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
                        self.oldx = self.oldx + 50
                    else:
                        self.display_surface.blit(self.statrenders[i], (self.player.rect.centerx - 1000 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - yoffset - (self.player.rect.centery - WINDOW_HEIGHT / 2)))

    def run(self):
        while self.running:
            #dt
            dt = self.clock.tick() / 1000

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event and self.enemys <= 20 * self.round and self.roundrunning:
                    enemy = choice(list(self.enemy_frames.keys()))
                    if self.round < 20 and (enemy == "blackspirit" or enemy == "skeletonspirit"):
                        enemy = enemy.replace("spirit", "fire")
                    if self.round < 15 and (enemy == "blackfire" or enemy == "skeletonfire"):
                        enemy = enemy.replace("fire", "ice")
                    if self.round < 10 and (enemy == "blackice" or enemy == "skeletonice"):
                        enemy = enemy.replace("ice", "brute")
                    if self.round < 5 and (enemy == "blackbrute" or enemy == "skeletonbrute"):
                        enemy = enemy.replace("brute", "")
                    tempenemy = Enemy(choice(self.spawn_positions), self.enemy_frames[enemy], (self.all_sprites, self.enemy_sprites), self.player, enemy, self.round, self.collision_sprites)
                    Health(tempenemy, (self.all_sprites, self.healthbars), self.healthlevels)
                    self.enemys += 1
                if event.type == self.score_event:
                    if self.roundrunning and self.round != 0:
                        self.roundtime += 1
                        self.score_time = self.time.render("Round " + str(self.round) + ": " + str((self.round * 10) - self.roundtime), True, (255, 255, 255))
                    else:
                        self.score_time = self.time.render("Upgrade", True, (255, 255, 255))

            # update
            self.playerhealthlevel = min(10, (10 - (int(self.player.health / self.player.maxhealth * 10))))
            self.checkround()
            self.upgradecheck()
            self.bullet_collision()
            self.player_collision()
            self.weapon_change()
            self.input()
            self.progression()
            self.gun_timer(self.shoot_time)
            self.all_sprites.update(dt)
            self.updatestats()

            self.display_surface.fill("black")
            self.all_sprites.draw(self.player.rect.center)

            self.display_surface.blit(self.scorebox, (self.player.rect.centerx - 200 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - 340 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
            if self.roundrunning and self.round != 0:
                self.display_surface.blit(self.score_time, (self.player.rect.centerx - 150 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - 330 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
            else:
                self.display_surface.blit(self.score_time, (self.player.rect.centerx - 100 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery - 330 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))
            self.checkcursor()
            self.upgradehover()
            self.display_surface.blit(self.playerhealthlevels[self.playerhealthlevel], (self.player.rect.centerx - 630 - (self.player.rect.centerx - WINDOW_WIDTH / 2),self.player.rect.centery + 275 - (self.player.rect.centery - WINDOW_HEIGHT / 2)))

            pygame.display.update()

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()

