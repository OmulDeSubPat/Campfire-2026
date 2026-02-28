import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
from meniu import ImageMenu
from character import Player
from backgorund import Background
from cutscene import SleepCutscene
from npc import NPC
from dialog import DialogBox

from combat import CombatPlayer, SkeletonEnemy, draw_hp_bar

TITLE = "Lost in Thought"
FPS = 60

MENU = "menu"
GAME = "game"
SETTINGS = "settings"
CUTSCENE = "cutscene"
BATTLE = "battle"

# ---------- PATHS (absolute, always correct) ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CHAR_DIR = os.path.join(BASE_DIR, "assetsCharacter")

def asset(*parts):
    return os.path.join(ASSETS_DIR, *parts)

def char_asset(*parts):
    return os.path.join(CHAR_DIR, *parts)

def require_file(path: str, label="file"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {label}: {path}")
    return path
# ------------------------------------------------------


# ✅ UPDATED DIALOG (your Matt text)
ROOM2_DIALOG = [
    {"speaker": "Narrator", "text": "(John sees Matt when he walks into the house)"},
    {"speaker": "John", "text": "What is this place? What are those houses? I want to take a look inside!"},
    {"speaker": "John", "text": "Wha-what?! Where am I? Who are you??"},
    {"speaker": "Matt", "text": "Well my dear friend, I am your fear of failure and you just stepped into my house."},
    {"speaker": "John", "text": "Am I dreaming or am I going insane??"},
    {"speaker": "Matt", "text": "John, calm down! You are here now, which means that you have to face a challenge and I will help you along your journey here!"},
    {"speaker": "John", "text": "Is there other way to get out?"},
    {"speaker": "Matt", "text": "Of course not :)! I will make sure that you will not forget this!"},
    {"speaker": "Matt", "text": "In the first challenge you will face the disappointment of your parents. You must defeat it. I will give you an advice!"},
    {"speaker": "Matt", "text": "Well my dear friend, my idea sounds like this: ignore every word they say and try to dominate."},
]


def new_game_world_room1(W, H):
    BG_W, BG_H = 2048, 1365
    sx, sy = W / BG_W, H / BG_H

    def R(x, y, w, h):
        return pygame.Rect(int(x * sx), int(y * sy), int(w * sx), int(h * sy))

    allowed_zone = R(820, 650, 460, 820)
    bed_collider = R(0, 0, 0, 0)

    spawn = (allowed_zone.centerx, allowed_zone.bottom - 10)
    player = Player(spawn)
    player.set_limits(allowed_zone, bed_collider)

    room_rect = pygame.Rect(0, 0, W, H)
    return room_rect, allowed_zone, bed_collider, player


def new_game_world_room2(W, H, player_existing: Player):
    room_rect = pygame.Rect(0, 0, W, H)
    allowed_zone = room_rect.inflate(-200, -200)
    bed_collider = pygame.Rect(0, 0, 0, 0)

    spawn = (allowed_zone.centerx, allowed_zone.bottom - 10)
    player_existing.hitbox.midbottom = spawn
    player_existing.rect.midbottom = spawn
    player_existing.set_limits(allowed_zone, bed_collider)

    npc_pos = (W // 2, 35)
    # ✅ matches your real filename
    npc2 = NPC(npc_pos, strip_name="Idle_caracter2.png", frames=6, scale=4.0, fps=8)

    return room_rect, allowed_zone, bed_collider, player_existing, npc2


def new_game_world_room3(W, H, player_existing: Player):
    room_rect = pygame.Rect(0, 0, W, H)
    allowed_zone = room_rect.inflate(-200, -200)
    bed_collider = pygame.Rect(0, 0, 0, 0)

    spawn = (allowed_zone.centerx, allowed_zone.bottom - 10)
    player_existing.hitbox.midbottom = spawn
    player_existing.rect.midbottom = spawn
    player_existing.set_limits(allowed_zone, bed_collider)

    return room_rect, allowed_zone, bed_collider, player_existing


def draw_settings(screen, W, H):
    screen.fill((18, 18, 22))
    font = pygame.font.SysFont("georgia", 56, bold=True)
    small = pygame.font.SysFont("georgia", 24)
    t = font.render("SETTINGS", True, (235, 235, 245))
    s = small.render("Press ESC to go back (prototype)", True, (180, 180, 195))
    screen.blit(t, t.get_rect(center=(W // 2, 160)))
    screen.blit(s, s.get_rect(center=(W // 2, 260)))


def draw_game(screen, bg: Background, player: Player, allowed_zone, bed_collider,
              npc=None, dialog=None, debug=True, room_name="room1"):
    bg.draw()

    if npc is not None:
        npc.draw(screen)

    player.draw(screen)

    if debug:
        pygame.draw.rect(screen, (0, 255, 0), allowed_zone, 2)
        pygame.draw.rect(screen, (255, 0, 0), bed_collider, 2)

    if dialog is not None and dialog.active and not dialog.done:
        dialog.draw(screen)

    hud_txt = f"{room_name.upper()} - ESC: menu | ENTER/SPACE: dialog"
    hud = pygame.font.SysFont(None, 24).render(hud_txt, True, (200, 200, 210))
    screen.blit(hud, (16, 12))


def start_music():
    candidates = [
        asset("muzicadefundal.ogg"),
        asset("muzicadefundal.mp3"),
        asset("muzicadefundal.wav"),
        asset("muzicadefundal.mpeg"),
    ]
    music_path = next((p for p in candidates if os.path.exists(p)), None)
    if music_path is None:
        raise FileNotFoundError("Missing music file. Tried:\n" + "\n".join(candidates))

    if pygame.mixer.get_init() is None:
        pygame.mixer.init(44100, -16, 2, 512)

    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)


def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption(TITLE)

    require_file(ASSETS_DIR, "assets folder")
    require_file(CHAR_DIR, "assetsCharacter folder")

    start_music()

    W, H = screen.get_size()
    clock = pygame.time.Clock()

    # ✅ matches your real filename
    menu = ImageMenu(screen, require_file(asset("Menu.png"), "menu image"))

    bg_room1 = Background(screen, require_file(asset("room.png"), "room1 background"))
    bg_room2 = Background(screen, require_file(asset("room2.png"), "room2 background"))
    bg_room3 = Background(screen, require_file(asset("room3.png"), "room3 background"))

    current_bg = bg_room1
    current_room = "room1"

    sleep_cs = SleepCutscene(
        (W, H),
        pulse_duration=3.5,
        pulses=4,
        max_alpha=235,
        fade_to_black_duration=1.0,
        hold_black_duration=0.7,
    )

    dialog = DialogBox((W, H), ROOM2_DIALOG, font_path=None, font_size=26, name_size=28, text_speed=45)

    state = MENU
    has_save = True

    room_rect, allowed_zone, bed_collider, player = new_game_world_room1(W, H)
    npc = None

    in_first_room = True
    cutscene_used_room1 = False
    room2_dialog_started = False
    room2_to_room3_triggered = False
    pending_wake_room = None

    # --- Battle objects ---
    battle_player = None
    battle_enemy = None
    battle_arena = pygame.Rect(80, 80, W - 160, H - 180)
    battle_started = False

    # ✅ enemy stays on the ground after death
    enemy_death_hold = 0.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        for e in events:
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if state == MENU:
                        running = False
                    else:
                        state = MENU

                if e.key == pygame.K_RETURN:
                    if state == GAME and current_room == "room1" and in_first_room and not cutscene_used_room1:
                        sleep_cs.start()
                        pending_wake_room = "room2"
                        state = CUTSCENE
                        cutscene_used_room1 = True
                    else:
                        if state == GAME and dialog.active and not dialog.done:
                            dialog.advance()

                if e.key == pygame.K_SPACE:
                    if state == GAME and dialog.active and not dialog.done:
                        dialog.advance()

        # --- UPDATE ---
        if state == MENU:
            action = menu.update(events, has_save)

            if action == "continue":
                state = GAME

            elif action == "new":
                current_bg = bg_room1
                current_room = "room1"
                room_rect, allowed_zone, bed_collider, player = new_game_world_room1(W, H)
                npc = None

                state = GAME
                has_save = True

                in_first_room = True
                cutscene_used_room1 = False
                room2_dialog_started = False
                room2_to_room3_triggered = False
                pending_wake_room = None

                dialog.active = False
                dialog.done = False

                battle_started = False
                battle_player = None
                battle_enemy = None
                enemy_death_hold = 0.0

            elif action == "settings":
                state = SETTINGS

            elif action == "quit":
                running = False

        elif state == GAME:
            if npc is not None:
                npc.update(dt)

            if dialog.active and not dialog.done:
                dialog.update(dt)
                if hasattr(dialog, "is_talking") and dialog.is_talking():
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.unpause()
                player.update(dt, None)

            if current_room == "room2" and room2_dialog_started and dialog.done and not room2_to_room3_triggered:
                room2_to_room3_triggered = True
                sleep_cs.start()
                pending_wake_room = "room3"
                state = CUTSCENE

            # ✅ battle starts in room3
            if current_room == "room3" and not battle_started:
                enemy_sheet = require_file(char_asset("Skeleton enemy.png"), "enemy sheet")

                battle_player = CombatPlayer((W * 0.35, H * 0.65), assets_dir=CHAR_DIR, scale=4.0)
                battle_enemy = SkeletonEnemy((W * 0.65, H * 0.65), sheet_path=enemy_sheet, scale=4.0)

                battle_started = True
                enemy_death_hold = 0.0
                state = BATTLE

        elif state == BATTLE:
            battle_player.update(dt, battle_arena, keys, battle_enemy)
            battle_enemy.update(dt, battle_arena, battle_player)

            # ✅ Enemy death: keep laying down (hold last death frame)
            if not battle_enemy.alive and battle_enemy.frame_idx >= len(battle_enemy.frames["death"]) - 1:
                if enemy_death_hold <= 0.0:
                    enemy_death_hold = 2.0  # seconds
                enemy_death_hold -= dt
                if enemy_death_hold <= 0.0:
                    state = GAME

            # Player death -> menu
            if not battle_player.alive and battle_player.frame_idx >= len(battle_player.frames["death"]) - 1:
                state = MENU

        elif state == CUTSCENE:
            sleep_cs.update(dt)
            if sleep_cs.done:
                if pending_wake_room == "room2":
                    current_bg = bg_room2
                    current_room = "room2"
                    room_rect, allowed_zone, bed_collider, player, npc = new_game_world_room2(W, H, player)
                    in_first_room = False
                    state = GAME

                    if not room2_dialog_started:
                        dialog.start()
                        room2_dialog_started = True

                elif pending_wake_room == "room3":
                    current_bg = bg_room3
                    current_room = "room3"
                    room_rect, allowed_zone, bed_collider, player = new_game_world_room3(W, H, player)
                    npc = None
                    state = GAME

                pending_wake_room = None

        # --- DRAW ---
        if state == MENU:
            menu.draw(has_save)

        elif state == SETTINGS:
            draw_settings(screen, W, H)

        elif state == GAME:
            draw_game(
                screen, current_bg, player,
                allowed_zone, bed_collider,
                npc=npc,
                dialog=dialog if current_room == "room2" else None,
                debug=True,
                room_name=current_room
            )

        elif state == CUTSCENE:
            draw_game(screen, current_bg, player, allowed_zone, bed_collider, npc=npc, dialog=None, debug=False, room_name=current_room)
            sleep_cs.draw(screen)

        elif state == BATTLE:
            current_bg.draw()
            pygame.draw.rect(screen, (200, 200, 210), battle_arena, 2)

            battle_enemy.draw(screen)
            battle_player.draw(screen)

            draw_hp_bar(screen, (40, 30, 280, 18), battle_player.hp, battle_player.max_hp, "JOHN")
            draw_hp_bar(screen, (W - 320, 30, 280, 18), battle_enemy.hp, battle_enemy.max_hp, "SKELETON")

            help_font = pygame.font.SysFont("georgia", 18, bold=True)
            tip = help_font.render("BATTLE: WASD to move | SHIFT run | J or K to attack", True, (235, 235, 230))
            screen.blit(tip, (40, H - 40))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        input("\nCrash happened. Press Enter to exit...")