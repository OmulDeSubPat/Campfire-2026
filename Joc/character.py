import os
import pygame
from pygame.math import Vector2
from typing import Optional

def load_strip(path: str, frames: int = 8, scale: float = 4.0):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing character strip: {path}")

    sheet = pygame.image.load(path).convert_alpha()
    w, h = sheet.get_size()

    frame_w = w // frames
    images = []
    for i in range(frames):
        rect = pygame.Rect(i * frame_w, 0, frame_w, h)
        frame = sheet.subsurface(rect).copy()
        if scale != 1:
            frame = pygame.transform.scale(frame, (int(frame_w * scale), int(h * scale)))
        images.append(frame)

    return images


class Player:
    def __init__(self, pos, speed_walk=220, speed_run=330, skin: str = "default"):
        self.skin = skin

        base = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base, "assetsCharacter")

        self.walk_frames = None
        self.run_frames = None
        self.idle_frames = None

        # default skin uses Walk/Run
        walk_path = os.path.join(assets_dir, "Walk.png")
        run_path = os.path.join(assets_dir, "Run.png")

        if skin == "caracter2":
            idle_path = os.path.join(assets_dir, "Idle_caracter2.png")
            if not os.path.exists(idle_path):
                raise FileNotFoundError(f"Missing: {idle_path}")

            self.idle_frames = load_strip(idle_path, frames=6, scale=4.0)
            self.image = self.idle_frames[0]
        else:
            if not os.path.exists(walk_path):
                raise FileNotFoundError(f"Missing: {walk_path}")
            if not os.path.exists(run_path):
                raise FileNotFoundError(f"Missing: {run_path}")

            self.walk_frames = load_strip(walk_path, frames=8, scale=4.0)
            self.run_frames = load_strip(run_path, frames=8, scale=4.0)
            self.image = self.walk_frames[0]

        self.rect = self.image.get_rect()
        self.rect.midbottom = (pos[0], pos[1])

        self.hitbox = pygame.Rect(0, 0, int(self.rect.w * 0.28), int(self.rect.h * 0.22))
        self.hitbox.midbottom = self.rect.midbottom

        self.speed_walk = speed_walk
        self.speed_run = speed_run

        self.anim_time = 0.0
        self.frame_idx = 0
        self.facing_right = True
        self.was_running = False
        self.walk_fps = 10
        self.run_fps = 14
        self.idle_fps = 8

        self.allowed_zone: Optional[pygame.Rect] = None
        self.bed_collider: Optional[pygame.Rect] = None

    def set_limits(self, allowed_zone: pygame.Rect, bed_collider: Optional[pygame.Rect] = None):
        self.allowed_zone = allowed_zone
        self.bed_collider = bed_collider

    def _handle_input(self):
        keys = pygame.key.get_pressed()
        vel = Vector2(0, 0)

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            vel.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            vel.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vel.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vel.x += 1

        running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if vel.length_squared() > 0:
            vel = vel.normalize()

        speed = self.speed_run if running else self.speed_walk
        vel *= speed
        return vel, running

    def _resolve_rect_collision(self, a: pygame.Rect, b: pygame.Rect):
        dx_left = b.right - a.left
        dx_right = a.right - b.left
        dy_top = b.bottom - a.top
        dy_bottom = a.bottom - b.top

        m = min(dx_left, dx_right, dy_top, dy_bottom)
        if m == dx_left:
            a.left = b.right
        elif m == dx_right:
            a.right = b.left
        elif m == dy_top:
            a.top = b.bottom
        else:
            a.bottom = b.top

    def _update_animation_default(self, dt: float, moving: bool, running: bool, vel: Vector2):
        if vel.x > 0:
            self.facing_right = True
        elif vel.x < 0:
            self.facing_right = False

        if running != self.was_running:
            self.was_running = running
            self.frame_idx = 0
            self.anim_time = 0.0

        if not moving:
            self.frame_idx = 0
            self.anim_time = 0.0
            self.image = self.walk_frames[0]
            return

        frames = self.run_frames if running else self.walk_frames
        fps = self.run_fps if running else self.walk_fps

        self.anim_time += dt
        frame_duration = 1.0 / fps
        while self.anim_time >= frame_duration:
            self.anim_time -= frame_duration
            self.frame_idx = (self.frame_idx + 1) % len(frames)

        self.image = frames[self.frame_idx]

    def _update_animation_idle_only(self, dt: float, vel: Vector2):
        if vel.x > 0:
            self.facing_right = True
        elif vel.x < 0:
            self.facing_right = False

        frames = self.idle_frames
        fps = self.idle_fps

        self.anim_time += dt
        frame_duration = 1.0 / fps
        while self.anim_time >= frame_duration:
            self.anim_time -= frame_duration
            self.frame_idx = (self.frame_idx + 1) % len(frames)

        self.image = frames[self.frame_idx]

    def update(self, dt, colliders_ignored):
        vel, running = self._handle_input()
        moving = vel.length_squared() > 0

        self.hitbox.x += int(vel.x * dt)
        self.hitbox.y += int(vel.y * dt)

        if self.allowed_zone is not None:
            self.hitbox.clamp_ip(self.allowed_zone)

        if self.bed_collider is not None and self.hitbox.colliderect(self.bed_collider):
            self._resolve_rect_collision(self.hitbox, self.bed_collider)
            if self.allowed_zone is not None:
                self.hitbox.clamp_ip(self.allowed_zone)

        self.rect.midbottom = self.hitbox.midbottom

        if self.skin == "caracter2":
            self._update_animation_idle_only(dt, vel)
        else:
            self._update_animation_default(dt, moving, running, vel)

    def draw(self, surface):
        img = self.image
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)

        draw_rect = img.get_rect(midbottom=self.rect.midbottom)
        surface.blit(img, draw_rect)