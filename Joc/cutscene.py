import math
import pygame


class SleepCutscene:
    """
    Sleep animation:
      1) Pulsing black overlay
      2) Fade to full black
      3) Hold full black
    """

    def __init__(
        self,
        size,
        pulse_duration=3.5,
        pulses=4,
        max_alpha=235,
        fade_to_black_duration=1.0,
        hold_black_duration=0.6,
    ):
        self.w, self.h = size

        self.pulse_duration = max(0.1, float(pulse_duration))
        self.pulses = max(1, int(pulses))
        self.max_alpha = max(0, min(255, int(max_alpha)))

        self.fade_to_black_duration = max(0.0, float(fade_to_black_duration))
        self.hold_black_duration = max(0.0, float(hold_black_duration))

        self.t = 0.0
        self.active = False
        self.done = False

        self.overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

    def start(self):
        self.t = 0.0
        self.active = True
        self.done = False

    def stop(self):
        self.active = False
        self.done = True

    def update(self, dt):
        if not self.active or self.done:
            return

        self.t += float(dt)

        total = self.pulse_duration + self.fade_to_black_duration + self.hold_black_duration
        if self.t >= total:
            self.t = total
            self.done = True
            self.active = False

    def _pulse_alpha(self, t):
        p = max(0.0, min(1.0, t / self.pulse_duration))
        wave = math.sin(p * math.pi * self.pulses)
        wave = max(0.0, wave)
        ramp = p ** 1.8
        a = (0.25 + 0.75 * ramp) * wave
        return int(a * self.max_alpha)

    def _alpha_at_time(self, t):
        if t <= self.pulse_duration:
            return self._pulse_alpha(t)

        t2 = t - self.pulse_duration

        if t2 <= self.fade_to_black_duration:
            if self.fade_to_black_duration <= 0:
                return 255
            k = max(0.0, min(1.0, t2 / self.fade_to_black_duration))
            return int(self.max_alpha + (255 - self.max_alpha) * k)

        return 255

    def draw(self, screen):
        if not (self.active or self.done):
            return

        alpha = self._alpha_at_time(self.t) if self.active else 255
        self.overlay.fill((0, 0, 0, alpha))
        screen.blit(self.overlay, (0, 0))