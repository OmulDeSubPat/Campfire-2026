import os
import pygame
from pygame.math import Vector2


def require_file(path: str, label="file"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {label}: {path}")
    return path


def load_strip(path: str, frames: int, scale: float = 4.0):
    require_file(path, "strip")
    sheet = pygame.image.load(path).convert_alpha()
    w, h = sheet.get_size()
    frame_w = w // frames

    images = []
    for i in range(frames):
        rect = pygame.Rect(i * frame_w, 0, frame_w, h)
        img = sheet.subsurface(rect).copy()
        if scale != 1:
            img = pygame.transform.scale(img, (int(frame_w * scale), int(h * scale)))
        images.append(img)
    return images


def load_grid_range(path: str, frame_w: int, frame_h: int, row: int, col_start: int, frames: int, scale: float = 4.0):
    require_file(path, "grid sheet")
    sheet = pygame.image.load(path).convert_alpha()
    sw, sh = sheet.get_size()

    max_cols = sw // frame_w
    max_rows = sh // frame_h

    if row < 0 or row >= max_rows:
        raise ValueError(f"{path}: row={row} out of range. rows={max_rows} (0..{max_rows-1})")
    if col_start < 0 or col_start >= max_cols:
        raise ValueError(f"{path}: col_start={col_start} out of range. cols={max_cols} (0..{max_cols-1})")
    if col_start + frames > max_cols:
        raise ValueError(f"{path}: col_start+frames={col_start+frames} exceeds cols={max_cols}")

    images = []
    y = row * frame_h
    for i in range(frames):
        x = (col_start + i) * frame_w
        rect = pygame.Rect(x, y, frame_w, frame_h)
        img = sheet.subsurface(rect).copy()
        if scale != 1:
            img = pygame.transform.scale(img, (int(frame_w * scale), int(frame_h * scale)))
        images.append(img)
    return images


class AnimatedActor:
    def __init__(self, pos, hp: int):
        self.pos = Vector2(pos)
        self.facing = 1

        self.hp = hp
        self.max_hp = hp
        self.alive = True

        self.frames = {}
        self.anim = "idle"
        self.fps = 10
        self.frame_idx = 0
        self.anim_time = 0.0

        self.image = None
        self.rect = pygame.Rect(0, 0, 1, 1)

        self.invuln = 0.0
        self.flash = 0.0

    def set_anim(self, name: str, fps: int, restart=False):
        if self.anim != name or restart:
            self.anim = name
            self.frame_idx = 0
            self.anim_time = 0.0
        self.fps = fps

    def take_damage(self, dmg: int):
        if not self.alive:
            return False
        if self.invuln > 0:
            return False

        self.hp -= dmg
        self.invuln = 0.35
        self.flash = 0.12

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return True

    def update_timers(self, dt: float):
        if self.invuln > 0:
            self.invuln = max(0.0, self.invuln - dt)
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

    def update_anim(self, dt: float, loop=False):
        frames = self.frames.get(self.anim, [])
        if not frames:
            return

        self.anim_time += dt
        frame_duration = 1.0 / max(1, self.fps)
        while self.anim_time >= frame_duration:
            self.anim_time -= frame_duration
            self.frame_idx += 1
            if self.frame_idx >= len(frames):
                self.frame_idx = 0 if loop else (len(frames) - 1)

        self.image = frames[self.frame_idx]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def draw(self, screen):
        if self.image is None:
            return
        img = self.image
        if self.facing < 0:
            img = pygame.transform.flip(img, True, False)
        screen.blit(img, img.get_rect(center=self.rect.center))


class CombatPlayer(AnimatedActor):
    def __init__(self, pos, assets_dir: str, scale: float = 4.0):
        super().__init__(pos, hp=100)

        self.IDLE_FRAMES = 6
        self.WALK_FRAMES = 8
        self.RUN_FRAMES = 8
        self.ATTACK_FRAMES = 6
        self.HURT_FRAMES = 4
        self.DEAD_FRAMES = 6

        self.speed_walk = 240
        self.speed_run = 330

        self.attack_damage = 18
        self.attack_cooldown = 0.0

        self.attack_active_from = 2
        self.attack_active_to = 4
        self._hit_this_swing = False

        self.frames["idle"] = load_strip(os.path.join(assets_dir, "Idle.png"), self.IDLE_FRAMES, scale)
        self.frames["walk"] = load_strip(os.path.join(assets_dir, "Walk.png"), self.WALK_FRAMES, scale)
        self.frames["run"] = load_strip(os.path.join(assets_dir, "Run.png"), self.RUN_FRAMES, scale)
        self.frames["attack"] = load_strip(os.path.join(assets_dir, "Attack_2.png"), self.ATTACK_FRAMES, scale)
        self.frames["hurt"] = load_strip(os.path.join(assets_dir, "Hurt.png"), self.HURT_FRAMES, scale)
        self.frames["death"] = load_strip(os.path.join(assets_dir, "Dead.png"), self.DEAD_FRAMES, scale)

        self.image = self.frames["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.set_anim("idle", fps=8, restart=True)

    def start_attack(self):
        if not self.alive:
            return
        if self.attack_cooldown > 0:
            return
        if self.anim in ("attack", "hurt", "death"):
            return

        self.set_anim("attack", fps=12, restart=True)
        self._hit_this_swing = False
        self.attack_cooldown = 0.45

    def _attack_hitbox(self):
        if self.anim != "attack":
            return None
        if self.frame_idx < self.attack_active_from or self.frame_idx > self.attack_active_to:
            return None
        w, h = 90, 70
        cx = self.rect.centerx + (50 if self.facing > 0 else -50)
        cy = self.rect.centery + 10
        r = pygame.Rect(0, 0, w, h)
        r.center = (cx, cy)
        return r

    def update(self, dt: float, arena: pygame.Rect, keys, enemy):
        self.update_timers(dt)
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if not self.alive:
            self.set_anim("death", fps=10)
            self.update_anim(dt, loop=False)
            return

        if self.invuln > 0 and self.anim != "hurt" and self.flash > 0:
            self.set_anim("hurt", fps=10, restart=True)

        if self.anim == "hurt":
            self.update_anim(dt, loop=False)
            if self.frame_idx >= len(self.frames["hurt"]) - 1:
                self.set_anim("idle", fps=8, restart=True)
            return

        v = Vector2(0, 0)
        moving = False
        running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if self.anim != "attack":
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                v.x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                v.x += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                v.y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                v.y += 1

            if v.length_squared() > 0:
                v = v.normalize()
                speed = self.speed_run if running else self.speed_walk
                self.pos += v * speed * dt
                moving = True
                if v.x != 0:
                    self.facing = 1 if v.x > 0 else -1

            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self.rect.clamp_ip(arena)
            self.pos.update(self.rect.center)

            self.set_anim("run" if (moving and running) else ("walk" if moving else "idle"),
                          fps=12 if running else 9)

        if keys[pygame.K_j] or keys[pygame.K_k]:
            self.start_attack()

        if self.anim == "attack":
            self.update_anim(dt, loop=False)
            hb = self._attack_hitbox()
            if hb and (not self._hit_this_swing) and enemy.alive and hb.colliderect(enemy.rect):
                enemy.take_damage(self.attack_damage)
                self._hit_this_swing = True

            if self.frame_idx >= len(self.frames["attack"]) - 1:
                self.set_anim("idle", fps=8, restart=True)
            return

        self.update_anim(dt, loop=True)


class SkeletonEnemy(AnimatedActor):
    def __init__(self, pos, sheet_path: str, scale: float = 4.0):
        super().__init__(pos, hp=80)

        # Your sheet: 832x320 => 13 cols x 5 rows of 64x64
        self.FRAME_W = 64
        self.FRAME_H = 64

        # Correct ranges for your image
        self.frames["walk"]   = load_grid_range(sheet_path, 64, 64, row=2, col_start=0, frames=4, scale=scale)
        self.frames["attack"] = load_grid_range(sheet_path, 64, 64, row=0, col_start=4, frames=4, scale=scale)
        self.frames["death"]  = load_grid_range(sheet_path, 64, 64, row=1, col_start=1, frames=6, scale=scale)
        self.frames["idle"]   = [self.frames["walk"][0]]

        self.speed = 170
        self.attack_range = 95
        self.attack_damage = 10
        self.attack_cooldown = 0.0
        self.attack_active_frame = 2
        self._hit_this_swing = False

        self.image = self.frames["idle"][0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.set_anim("walk", fps=8, restart=True)

    def start_attack(self):
        if not self.alive:
            return
        if self.attack_cooldown > 0:
            return
        if self.anim == "attack":
            return
        self.set_anim("attack", fps=10, restart=True)
        self._hit_this_swing = False
        self.attack_cooldown = 0.9

    def _attack_hitbox(self):
        if self.anim != "attack":
            return None
        if self.frame_idx != self.attack_active_frame:
            return None
        w, h = 85, 70
        cx = self.rect.centerx + (40 if self.facing > 0 else -40)
        cy = self.rect.centery + 10
        r = pygame.Rect(0, 0, w, h)
        r.center = (cx, cy)
        return r

    def update(self, dt: float, arena: pygame.Rect, player: CombatPlayer):
        self.update_timers(dt)
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        if not self.alive:
            self.set_anim("death", fps=8)
            self.update_anim(dt, loop=False)
            return

        dx = player.pos.x - self.pos.x
        self.facing = 1 if dx > 0 else -1
        dist = abs(dx)

        if self.anim == "attack":
            self.update_anim(dt, loop=False)
            hb = self._attack_hitbox()
            if hb and (not self._hit_this_swing) and player.alive and hb.colliderect(player.rect):
                player.take_damage(self.attack_damage)
                self._hit_this_swing = True

            if self.frame_idx >= len(self.frames["attack"]) - 1:
                self.set_anim("walk", fps=8, restart=True)
            return

        if dist <= self.attack_range:
            self.start_attack()
            self.update_anim(dt, loop=False)
            return

        dir_vec = Vector2(player.pos.x - self.pos.x, player.pos.y - self.pos.y)
        if dir_vec.length_squared() > 0:
            dir_vec = dir_vec.normalize()
            self.pos += dir_vec * self.speed * dt

        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.rect.clamp_ip(arena)
        self.pos.update(self.rect.center)

        self.set_anim("walk", fps=8)
        self.update_anim(dt, loop=True)


def draw_hp_bar(screen, *args):
    if len(args) >= 4 and isinstance(args[0], (tuple, list)):
        x, y, w, h = args[0]
        hp = args[1]
        max_hp = args[2]
        label = args[3] if len(args) >= 4 else ""
    else:
        x, y, w, h, hp, max_hp = args[:6]
        label = args[6] if len(args) >= 7 else ""

    pygame.draw.rect(screen, (20, 20, 25), (x, y, w, h))
    pct = 0 if max_hp <= 0 else max(0.0, min(1.0, hp / max_hp))
    pygame.draw.rect(screen, (180, 40, 40), (x, y, int(w * pct), h))
    pygame.draw.rect(screen, (230, 230, 220), (x, y, w, h), 2)

    if label:
        font = pygame.font.SysFont("georgia", 18, bold=True)
        t = font.render(label, True, (235, 235, 230))
        screen.blit(t, (x, y - 20))