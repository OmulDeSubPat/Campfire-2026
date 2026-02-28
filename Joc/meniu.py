import os
import pygame

class ImageMenu:
    def __init__(self, screen, image_path):
        self.screen = screen
        self.W, self.H = screen.get_size()

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing menu image: {image_path}")

        self.bg_original = pygame.image.load(image_path).convert()
        self.bg = pygame.transform.smoothscale(self.bg_original, (self.W, self.H))

        self.rel_buttons = {
            "continue": (0.298, 0.356, 0.404, 0.075),
            "new":      (0.298, 0.438, 0.404, 0.075),
            "settings": (0.298, 0.551, 0.404, 0.075),
            "quit":     (0.298, 0.633, 0.404, 0.075),
        }

        self.buttons = {}
        self._build_rects()

        self.focus_order = ["continue", "new", "settings", "quit"]
        self.focus_idx = 0
        self.hovered = None

    def _build_rects(self):
        self.buttons = {}
        for name, (rx, ry, rw, rh) in self.rel_buttons.items():
            rect = pygame.Rect(
                int(rx * self.W),
                int(ry * self.H),
                int(rw * self.W),
                int(rh * self.H),
            )
            self.buttons[name] = rect

    def update(self, events, has_save=True):
        mouse = pygame.mouse.get_pos()
        self.hovered = None

        for name, r in self.buttons.items():
            if r.collidepoint(mouse):
                if name == "continue" and not has_save:
                    continue
                self.hovered = name
                break

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_DOWN, pygame.K_TAB):
                    self.focus_idx = (self.focus_idx + 1) % 4
                elif e.key == pygame.K_UP:
                    self.focus_idx = (self.focus_idx - 1) % 4

                if e.key == pygame.K_n:
                    return "new"
                if e.key == pygame.K_s:
                    return "settings"
                if e.key == pygame.K_q:
                    return "quit"

                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    choice = self.focus_order[self.focus_idx]
                    if choice == "continue" and not has_save:
                        return None
                    return choice

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.hovered:
                    return self.hovered

        return None

    def draw(self, has_save=True):
        self.screen.blit(self.bg, (0, 0))

        highlight = self.hovered or self.focus_order[self.focus_idx]
        if highlight == "continue" and not has_save:
            highlight = None

        if highlight:
            r = self.buttons[highlight]
            overlay = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            overlay.fill((255, 220, 150, 40))
            self.screen.blit(overlay, r.topleft)