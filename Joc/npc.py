import os
import pygame

def load_strip(path: str, frames: int = 6, scale: float = 4.0):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing NPC strip: {path}")

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


class NPC:
    def __init__(self, pos_midtop, strip_name="Idle_caracter2.png", frames=6, scale=4.0, fps=8):
        base = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base, "assetsCharacter")

        candidates = [
            os.path.join(assets_dir, strip_name),
            os.path.join(assets_dir, "Idle_caracter2.png"),
            os.path.join(assets_dir, "idle_caracter2.png"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if path is None:
            raise FileNotFoundError("Missing NPC strip. Tried:\n" + "\n".join(candidates))

        self.frames = load_strip(path, frames=frames, scale=scale)
        self.fps = fps

        self.anim_time = 0.0
        self.frame_idx = 0
        self.image = self.frames[0]

        self.rect = self.image.get_rect()
        self.rect.midtop = pos_midtop

    def update(self, dt: float):
        self.anim_time += float(dt)
        frame_duration = 1.0 / max(1, self.fps)
        while self.anim_time >= frame_duration:
            self.anim_time -= frame_duration
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        self.image = self.frames[self.frame_idx]

    def draw(self, screen):
        screen.blit(self.image, self.rect)