import os
import pygame

class Background:
    def __init__(self, screen, image_path):
        self.screen = screen
        self.image_path = image_path

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing background image: {image_path}")

        self.original = pygame.image.load(image_path).convert()
        self.scaled = None
        self._last_size = None

    def _ensure_scaled(self):
        size = self.screen.get_size()
        if size != self._last_size:
            self.scaled = pygame.transform.smoothscale(self.original, size)
            self._last_size = size

    def draw(self):
        self._ensure_scaled()
        self.screen.blit(self.scaled, (0, 0))