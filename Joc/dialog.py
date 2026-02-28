import os
import pygame


def wrap_text(text: str, font: pygame.font.Font, max_width: int):
    words = text.split(" ")
    lines = []
    cur = ""

    for w in words:
        test = w if not cur else cur + " " + w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class DialogBox:
    def __init__(
        self,
        screen_size,
        lines,
        font_path=None,
        font_size=26,
        name_size=28,
        text_speed=45,
        box_height_ratio=0.24
    ):
        self.W, self.H = screen_size
        self.lines = lines
        self.idx = 0

        self.text_speed = float(text_speed)
        self.char_count = 0.0
        self.finished_line = False
        self.done = False
        self.active = False

        # -------- Load sound --------
        base = os.path.dirname(__file__)
        sound_path = os.path.join(base, "assets", "vocal.mp3")

        self.voice_sound = None
        if os.path.exists(sound_path):
            try:
                self.voice_sound = pygame.mixer.Sound(sound_path)
                self.voice_sound.set_volume(0.4)
            except:
                print("Could not load vocal.mp3")

        self.voice_playing = False

        # Fonts
        self.font = self._load_font(font_path, font_size)
        self.name_font = self._load_font(font_path, name_size, bold=True)

        # Box geometry
        self.box_h = int(self.H * box_height_ratio)
        self.box_rect = pygame.Rect(24, self.H - self.box_h - 24, self.W - 48, self.box_h)

        self.bg_color = (10, 10, 12)
        self.border_color = (220, 220, 210)
        self.text_color = (235, 235, 225)
        self.name_color = (240, 220, 170)

        self._current_full_text = ""
        self._current_speaker = None

    def _load_font(self, font_path, size, bold=False):
        if font_path and os.path.exists(font_path):
            f = pygame.font.Font(font_path, size)
            f.set_bold(bold)
            return f

        f = pygame.font.SysFont("georgia", size, bold=bold)
        return f

    def start(self):
        self.active = True
        self.done = False
        self.idx = 0
        self._load_current_line()

    def _load_current_line(self):
        if self.idx >= len(self.lines):
            self.done = True
            self.active = False
            self._stop_voice()
            return

        item = self.lines[self.idx]
        self._current_speaker = item.get("speaker", None)
        self._current_full_text = item.get("text", "")

        self.char_count = 0.0
        self.finished_line = False

        self._start_voice()

    def _start_voice(self):
        if self.voice_sound and not self.voice_playing:
            self.voice_sound.play(-1)
            self.voice_playing = True

    def _stop_voice(self):
        if self.voice_sound and self.voice_playing:
            self.voice_sound.stop()
            self.voice_playing = False

    def update(self, dt):
        if not self.active or self.done:
            return

        if self.finished_line:
            return

        self.char_count += self.text_speed * float(dt)

        if self.char_count >= len(self._current_full_text):
            self.char_count = float(len(self._current_full_text))
            self.finished_line = True
            self._stop_voice()

    def advance(self):
        if not self.active or self.done:
            return

        if not self.finished_line:
            self.char_count = float(len(self._current_full_text))
            self.finished_line = True
            self._stop_voice()
            return

        self.idx += 1
        self._load_current_line()

    def draw(self, screen):
        if not self.active or self.done:
            return

        pygame.draw.rect(screen, self.bg_color, self.box_rect, border_radius=6)
        pygame.draw.rect(screen, self.border_color, self.box_rect, width=3, border_radius=6)

        pad = 18
        x = self.box_rect.x + pad
        y = self.box_rect.y + pad

        if self._current_speaker:
            name_surf = self.name_font.render(f"{self._current_speaker}:", True, self.name_color)
            screen.blit(name_surf, (x, y))
            y += name_surf.get_height() + 8

        shown = self._current_full_text[: int(self.char_count)]
        max_text_w = self.box_rect.w - pad * 2
        lines = wrap_text(shown, self.font, max_text_w)

        for line in lines[:6]:
            surf = self.font.render(line, True, self.text_color)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 4

        if self.finished_line:
            prompt = self.font.render("▶", True, self.text_color)
            screen.blit(prompt, (
                self.box_rect.right - pad - prompt.get_width(),
                self.box_rect.bottom - pad - prompt.get_height()
            ))