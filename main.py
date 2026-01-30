
import arcade
import os
import math
import time

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

PATH = os.path.dirname(os.path.abspath(__file__))

# Окно и физика
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Joestars Revenge!"

MOVEMENT_SPEED = 5
JUMP_SPEED = 20
GRAVITY = 0.9

# Состояния
STATE_MENU = 0
STATE_GAME = 1
STATE_GAME_OVER = 2
STATE_VICTORY = 3

# Файлы для меню / gameover / victory (опционально)
MENU_BG_FILE = "menu_bg.jpg"
GAMEOVER_BG_FILE = "gameover_bg.jpg"
VICTORY_BG_FILE = "victory_bg.jpg"

# Уровни
LEVELS = [
    {
        "name": "Level 1",
        "background": "background.jpg",
        "platform_texture": "platform.png",
        "exp_texture": "exp.png",
        "transition_locked": "transition_locked.png",
        "transition_unlocked": "transition_unlocked.png",
        "walls": [
            (0, 16), (64, 16), (128, 16), (192, 16), (256, 16), (320, 16), (384, 16),
            (600, 100), (664, 100), (800, 200), (864, 200),
            (1200, 16), (1264, 16), (1328, 16), (1392, 16), (1392, 80)
        ],
        "plats": [(450, 120, 3), (1000, 250, -2)],
        "exp": [(200, 100), (630, 150), (830, 250), (1300, 100)],
        "special_items": [
            {"name": "caesar_band", "x": 400, "y": 180, "texture": "caesar_band.png"}
        ],
        "start": (100, 150),
    },
    {
        "name": "Level 2",
        "background": "background2.jpg",
        "platform_texture": "platform.png",
        "exp_texture": "exp.png",
        "transition_locked": "transition_locked.png",
        "transition_unlocked": "transition_unlocked.png",
        "walls": [
            (0, 16), (64, 16), (128, 16), (192, 16), (256, 16), (320, 16),
            (500, 50), (560, 50), (620, 50), (900, 120), (960, 120)
        ],
        "plats": [(600, 180, 2), (1100, 220, -3)],
        "exp": [(300, 120), (700, 200), (1150, 240)],
        "npcs": [
            {"x": 600, "y": 200, "texture": "zombie_lvl2.png"},
            {"x": 1100, "y": 240, "texture": "zombie_lvl2.png"},
        ],
        "start": (80, 150),
    },
    {
        "name": "Level 3",
        "background": "background3.jpg",
        "platform_texture": "platform.png",
        "exp_texture": "exp.png",
        "transition_locked": "transition_locked.png",
        "transition_unlocked": "transition_unlocked.png",
        "walls": [
            (0, 16), (64, 16), (128, 16), (192, 16), (256, 16), (320, 16),
            (700, 120), (760, 120), (820, 120), (1100, 160), (1160, 160)
        ],
        "plats": [(500, 220, 2), (900, 300, -2), (1250, 200, 3)],
        "exp": [(250, 180), (680, 260), (980, 340), (1300, 200)],
        "npcs": [
            {"x": 500, "y": 242, "texture": "zombie_lvl3.png"},
            {"x": 900, "y": 322, "texture": "zombie_lvl3.png"},
        ],
        "boss": {"x": 1300, "y": 240, "texture": "kars.png", "hp": 5, "damage": 3},
        "start": (60, 150),
    },
]


def make_flipped_copy(filename: str) -> str:
    src = os.path.join(PATH, filename)
    flipped_name = f"_flipped_{filename}"
    dst = os.path.join(PATH, flipped_name)

    if not os.path.exists(src):
        return None
    if os.path.exists(dst):
        return dst
    if PIL_AVAILABLE:
        try:
            img = Image.open(src).convert("RGBA")
            img_flipped = ImageOps.mirror(img)
            img_flipped.save(dst)
            return dst
        except Exception:
            return None
    return None


def load_texture_pair(filename: str):
    src = os.path.join(PATH, filename)
    if not os.path.exists(src):
        return None, None
    try:
        tex_r = arcade.load_texture(src)
    except Exception:
        tex_r = None

    tex_l = None
    flipped_path = make_flipped_copy(filename)
    if flipped_path and os.path.exists(flipped_path):
        try:
            tex_l = arcade.load_texture(flipped_path)
        except Exception:
            tex_l = None

    if tex_l is None:
        try:
            tex_l = arcade.load_texture(src, mirrored=True)
        except Exception:
            tex_l = None

    if tex_l is None:
        tex_l = tex_r

    return tex_r, tex_l


class NPC(arcade.Sprite):
    def __init__(self, texture_file, x, y, left_bound, right_bound, speed=1.5, hp=1, damage=1, is_boss=False):
        # Используем файл текстуры если он есть
        full_path = os.path.join(PATH, texture_file) if texture_file else None
        if full_path and os.path.exists(full_path):
            try:
                super().__init__(full_path)
            except Exception:
                super().__init__()
                # запасная текстура
                self.texture = arcade.make_soft_square_texture(32, arcade.color.DARK_GREEN, outer_alpha=255)
        else:
            super().__init__()
            self.texture = arcade.make_soft_square_texture(32, arcade.color.DARK_GREEN, outer_alpha=255)

        self.center_x = x
        self.center_y = y
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.change_x = speed
        self.speed = speed
        self.hp = hp
        self.damage = damage
        self.is_boss = is_boss
        self.last_hit_time = 0.0

    def update(self):
        # простая патрульная логика
        self.center_x += self.change_x
        if self.center_x < self.left_bound or self.center_x > self.right_bound:
            self.change_x *= -1


def create_projectile(texture_file, x, y, vx, vy, lifetime=2.5):
    full_path = os.path.join(PATH, texture_file) if texture_file else None
    if full_path and os.path.exists(full_path):
        try:
            proj = arcade.Sprite(full_path)
        except Exception:
            proj = arcade.SpriteSolidColor(8, 8, arcade.color.WHITE)
    else:
        proj = arcade.SpriteSolidColor(8, 8, arcade.color.WHITE)

    proj.center_x = x
    proj.center_y = y
    proj.change_x = vx
    proj.change_y = vy
    proj.spawn_time = time.time()
    proj.lifetime = lifetime
    return proj


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Спрайты
        self.player_list = None
        self.wall_list = None
        self.platform_list = None
        self.exp_list = None
        self.bg_list = None
        self.transition_list = None
        self.special_item_list = None
        self.npc_list = None
        self.projectile_list = None

        # Игрок
        self.player = None
        self.player_textures = None
        self.player_facing = "right"

        # Камера
        try:

            self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        except Exception:
            # fallback to None
            self.camera = None
            self.gui_camera = None
        self.zoom_level = 1.0


        self.state = STATE_MENU
        self.exp_score = 0
        self.lives = 3


        self.level_index = 0

        # Чекпоинты
        self.start_x, self.start_y = 100, 150
        self.respawn_x, self.respawn_y = self.start_x, self.start_y

        # Анимация
        self.animation_timer = 0.0
        self.animation_interval = 0.12
        self.walk_frame = 0

        # Музыка
        self.music_path = None
        for f in os.listdir(PATH):
            if f.lower().endswith(".mp3"):
                self.music_path = os.path.join(PATH, f)
                break
        self.music_sound = None
        self.music_player = None
        self.music_volume = 0.6
        self.music_muted = False

        self.menu_bg_list = arcade.SpriteList()
        mpath = os.path.join(PATH, MENU_BG_FILE)
        if os.path.exists(mpath):
            try:
                s = arcade.Sprite(mpath)
                s.center_x = SCREEN_WIDTH / 2
                s.center_y = SCREEN_HEIGHT / 2
                s.width = SCREEN_WIDTH
                s.height = SCREEN_HEIGHT
                self.menu_bg_list.append(s)
            except Exception:
                self.menu_bg_list = arcade.SpriteList()

        self.gameover_bg_list = arcade.SpriteList()
        gpath = os.path.join(PATH, GAMEOVER_BG_FILE)
        if os.path.exists(gpath):
            try:
                s = arcade.Sprite(gpath)
                s.center_x = SCREEN_WIDTH / 2
                s.center_y = SCREEN_HEIGHT / 2
                s.width = SCREEN_WIDTH
                s.height = SCREEN_HEIGHT
                self.gameover_bg_list.append(s)
            except Exception:
                self.gameover_bg_list = arcade.SpriteList()

        self.victory_bg_list = arcade.SpriteList()
        vpath = os.path.join(PATH, VICTORY_BG_FILE)
        if os.path.exists(vpath):
            try:
                s = arcade.Sprite(vpath)
                s.center_x = SCREEN_WIDTH / 2
                s.center_y = SCREEN_HEIGHT / 2
                s.width = SCREEN_WIDTH
                s.height = SCREEN_HEIGHT
                self.victory_bg_list.append(s)
            except Exception:
                self.victory_bg_list = arcade.SpriteList()


        self.projectile_texture = "projectile.png"


        self.has_caesar = False
        self.shoot_cooldown = 0.25
        self._last_shot_time = 0.0

    # ---------------- Music helpers ----------------
    def _stop_music(self):
        if self.music_player:
            try:
                if hasattr(self.music_player, "stop"):
                    self.music_player.stop()
                elif hasattr(self.music_player, "pause"):
                    self.music_player.pause()
            except Exception:
                pass
        self.music_player = None
        self.music_sound = None

    def _play_music(self):
        self._stop_music()
        if not self.music_path:
            return
        try:
            self.music_sound = arcade.load_sound(self.music_path)
            try:
                self.music_player = self.music_sound.play(loop=True, volume=(0.0 if self.music_muted else self.music_volume))
            except TypeError:
                try:
                    self.music_player = self.music_sound.play(volume=(0.0 if self.music_muted else self.music_volume))
                except Exception:
                    self.music_player = self.music_sound.play()
            except Exception:
                self.music_player = self.music_sound.play()
        except Exception:
            try:
                import pyglet
                source = pyglet.media.load(self.music_path)
                player = pyglet.media.Player()
                player.queue(source)
                try:
                    player.volume = 0.0 if self.music_muted else self.music_volume
                except Exception:
                    pass
                try:
                    player.loop = True
                except Exception:
                    pass
                player.play()
                self.music_player = player
            except Exception:
                self.music_player = None

    def _update_music_volume(self):
        if self.music_player is None and self.music_path:
            self._play_music()
            return
        try:
            if hasattr(self.music_player, "volume"):
                self.music_player.volume = 0.0 if self.music_muted else self.music_volume
                return
            self._play_music()
        except Exception:
            try:
                self._play_music()
            except Exception:
                pass

    def setup(self, level_index: int = 0):
        if level_index < 0:
            level_index = 0
        if level_index >= len(LEVELS):
            level_index = 0
        self.level_index = level_index
        level = LEVELS[self.level_index]

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.platform_list = arcade.SpriteList()
        self.exp_list = arcade.SpriteList()
        self.bg_list = arcade.SpriteList()
        self.transition_list = arcade.SpriteList()
        self.special_item_list = arcade.SpriteList()
        self.npc_list = arcade.SpriteList()
        self.projectile_list = arcade.SpriteList()

        try:
            if not self.camera:
                self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
            if not self.gui_camera:
                self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        except Exception:
            pass
        self.zoom_level = 1.0


        self.exp_score = 0
        self.lives = 3
        self.start_x, self.start_y = level.get("start", (100, 150))
        self.respawn_x, self.respawn_y = self.start_x, self.start_y


        self.has_caesar = False
        self._last_shot_time = 0.0


        bg_file = level.get("background")
        if bg_file:
            bg_path = os.path.join(PATH, bg_file)
            if os.path.exists(bg_path):
                try:
                    bg_sprite = arcade.Sprite(bg_path)
                    bg_sprite.center_x = SCREEN_WIDTH / 2
                    bg_sprite.center_y = SCREEN_HEIGHT / 2
                    bg_sprite.width = SCREEN_WIDTH
                    bg_sprite.height = SCREEN_HEIGHT
                    self.bg_list.append(bg_sprite)
                except Exception:
                    self.bg_list = arcade.SpriteList()

        # Player textures
        stand_r, stand_l = load_texture_pair("Stand.png")
        walk_r, walk_l = load_texture_pair("Walk.png")
        jump_r, jump_l = load_texture_pair("Jump.png")

        if stand_r is None and walk_r is None and jump_r is None:
            self.player_textures = None
            self.player = arcade.SpriteSolidColor(40, 60, arcade.color.BLUE)
        else:
            def safe(a, b, c=None):
                return a or b or c
            self.player_textures = {
                "right": {
                    "stand": safe(stand_r, walk_r, jump_r),
                    "walk": safe(walk_r, stand_r, jump_r),
                    "jump": safe(jump_r, stand_r, walk_r)
                },
                "left": {
                    "stand": safe(stand_l, walk_l, walk_l),
                    "walk": safe(walk_l, stand_l, walk_l),
                    "jump": safe(jump_l, stand_l, walk_l)
                }
            }
            self.player = arcade.Sprite()
            # Гарантируем, что texture не None:
            tex0 = self.player_textures["right"].get("stand")
            if tex0 is not None:
                self.player.texture = tex0
            else:
                # запасной внешний вид
                self.player = arcade.SpriteSolidColor(40, 60, arcade.color.BLUE)
                self.player_textures = None


        self.player.center_x, self.player.center_y = self.respawn_x, self.respawn_y
        self.player.change_x = 0
        self.player.change_y = 0
        self.player_list.append(self.player)

        # Walls
        for x, y in level.get("walls", []):
            w = arcade.SpriteSolidColor(64, 32, arcade.color.GRAY)
            w.center_x, w.center_y = x, y
            self.wall_list.append(w)


        platform_tex = level.get("platform_texture")
        for x, y, sx in level.get("plats", []):
            if platform_tex and os.path.exists(os.path.join(PATH, platform_tex)):
                try:
                    p = arcade.Sprite(os.path.join(PATH, platform_tex))
                    p.width = 120
                    p.height = 20
                except Exception:
                    p = arcade.SpriteSolidColor(120, 20, arcade.color.RED)
            else:
                p = arcade.SpriteSolidColor(120, 20, arcade.color.RED)
            p.center_x, p.center_y = x, y
            p.change_x = sx
            p.bound_left = x - 300
            p.bound_right = x + 300
            self.platform_list.append(p)


        exp_tex = level.get("exp_texture")
        for x, y in level.get("exp", []):
            if exp_tex and os.path.exists(os.path.join(PATH, exp_tex)):
                try:
                    e = arcade.Sprite(os.path.join(PATH, exp_tex))
                    e.width = 20
                    e.height = 20
                except Exception:
                    e = arcade.SpriteSolidColor(20, 20, arcade.color.GOLD)
            else:
                e = arcade.SpriteSolidColor(20, 20, arcade.color.GOLD)
            e.center_x, e.center_y = x, y
            e.value = 5
            self.exp_list.append(e)


        for itm in level.get("special_items", []):
            tex = itm.get("texture")
            if tex and os.path.exists(os.path.join(PATH, tex)):
                try:
                    s = arcade.Sprite(os.path.join(PATH, tex))
                    s.width = 24
                    s.height = 24
                except Exception:
                    s = arcade.SpriteSolidColor(24, 24, arcade.color.LIGHT_GRAY)
            else:
                s = arcade.SpriteSolidColor(24, 24, arcade.color.LIGHT_GRAY)
            s.center_x = itm.get("x", 0)
            s.center_y = itm.get("y", 0)
            s.item_name = itm.get("name")
            self.special_item_list.append(s)


        t_locked = level.get("transition_locked")
        t_unlocked = level.get("transition_unlocked")
        transitions = level.get("transition")
        if transitions is None:

            max_x = self.start_x
            for lst in (level.get("walls", []), level.get("plats", []), level.get("exp", [])):
                for item in lst:
                    if len(item) >= 1:
                        try:
                            ix = item[0]
                            if isinstance(ix, (int, float)) and ix > max_x:
                                max_x = ix
                        except Exception:
                            pass
            tx = max_x + 200
            ty = 80
            transitions = [(tx, ty)]
        for tx, ty in transitions:
            if t_locked and os.path.exists(os.path.join(PATH, t_locked)):
                t = arcade.Sprite(os.path.join(PATH, t_locked))
                t.width = 48
                t.height = 64
            else:
                t = arcade.SpriteSolidColor(48, 64, arcade.color.RED)
            t.center_x, t.center_y = tx, ty
            t.locked = True
            t.locked_tex = t_locked
            t.unlocked_tex = t_unlocked
            self.transition_list.append(t)

        # NPCs
        for npc_def in level.get("npcs", []):
            nx = npc_def.get("x")
            ny = npc_def.get("y")
            ntex = npc_def.get("texture")

            left_b = nx - 200
            right_b = nx + 200
            for p in self.platform_list:

                if abs((p.center_y + (p.height / 2)) - ny) < 24 and (p.left - 1) <= nx <= (p.right + 1):
                    left_b = getattr(p, "bound_left", p.center_x - p.width / 2)
                    right_b = getattr(p, "bound_right", p.center_x + p.width / 2)
                    break
            npc = NPC(ntex, nx, ny, left_b, right_b, speed=1.2, hp=1, damage=1, is_boss=False)
            self.npc_list.append(npc)

        # Boss (Kars) level 3
        boss_def = level.get("boss")
        if boss_def:
            bx = boss_def.get("x")
            by = boss_def.get("y")
            btex = boss_def.get("texture")
            bhp = boss_def.get("hp", 5)
            bdamage = boss_def.get("damage", 3)

            left_b = bx - 50
            right_b = bx + 50
            for p in self.platform_list:
                if abs((p.center_y + (p.height / 2)) - by) < 32 and (p.left - 1) <= bx <= (p.right + 1):
                    left_b = getattr(p, "bound_left", p.center_x - p.width / 2)
                    right_b = getattr(p, "bound_right", p.center_x + p.width / 2)
                    break
            boss = NPC(btex, bx, by, left_b, right_b, speed=0.6, hp=bhp, damage=bdamage, is_boss=True)

            self.npc_list.append(boss)


        self.animation_timer = 0.0
        self.walk_frame = 0
        self.player_facing = "right"

        self._update_music_volume()


    def on_draw(self):
        self.clear()


        if self.gui_camera:
            try:
                self.gui_camera.use()
            except Exception:
                pass

        if self.state == STATE_MENU:
            if len(self.menu_bg_list) > 0:
                self.menu_bg_list.draw()
            arcade.draw_text("JOESTARS REVENGE!", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40,
                             arcade.color.WHITE, 48, anchor_x="center")
            arcade.draw_text("Нажмите ENTER для начала", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
                             arcade.color.YELLOW, 22, anchor_x="center")
            arcade.draw_text("Z/X — зум | A/D или стрелки — движение | SPACE — прыжок", SCREEN_WIDTH / 2,
                             SCREEN_HEIGHT / 2 - 60, arcade.color.LIGHT_GRAY, 14, anchor_x="center")
            arcade.draw_text("., — регулировка громкости | M — mute/unmute", SCREEN_WIDTH / 2,
                             SCREEN_HEIGHT / 2 - 86, arcade.color.LIGHT_GRAY, 12, anchor_x="center")
            return

        if self.state == STATE_GAME:
            if self.bg_list:

                if self.gui_camera:
                    try:
                        self.gui_camera.use()
                    except Exception:
                        pass
                self.bg_list.draw()


            self.scroll_to_player()

            if self.wall_list:
                self.wall_list.draw()
            if self.platform_list:
                self.platform_list.draw()
            if self.transition_list:
                self.transition_list.draw()
            if self.exp_list:
                self.exp_list.draw()
            if self.special_item_list:
                self.special_item_list.draw()
            if self.npc_list:
                self.npc_list.draw()
            if self.player_list:
                self.player_list.draw()
            if self.projectile_list:
                self.projectile_list.draw()


            if self.gui_camera:
                try:
                    self.gui_camera.use()
                except Exception:
                    pass
            level_name = LEVELS[self.level_index].get("name", f"Level {self.level_index+1}")
            vol_text = "MUTED" if self.music_muted else f"{int(self.music_volume*100)}%"
            arcade.draw_text(f"{level_name} | EXP: {self.exp_score} | LIVES: {self.lives} | ZOOM: {self.zoom_level:.1f} | VOL: {vol_text}",
                             20, SCREEN_HEIGHT - 36, arcade.color.WHITE, 18)


            if self.has_caesar:
                hint = "LMB — стрелять (тратит 1 EXP)"
                arcade.draw_text(hint, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 30, arcade.color.YELLOW, 16, anchor_x="right")
            return

        if self.state == STATE_GAME_OVER:
            if len(self.gameover_bg_list) > 0:
                self.gameover_bg_list.draw()
            arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20,
                             arcade.color.RED, 56, anchor_x="center")
            arcade.draw_text("Нажмите R для рестарта уровня", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                             arcade.color.WHITE, 20, anchor_x="center")
            return

        if self.state == STATE_VICTORY:
            if len(self.victory_bg_list) > 0:
                self.victory_bg_list.draw()
            arcade.draw_text("YOU WIN!", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20,
                             arcade.color.GREEN, 56, anchor_x="center")
            arcade.draw_text("Нажмите ENTER для возвращения в меню", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
                             arcade.color.WHITE, 20, anchor_x="center")
            return


    def scroll_to_player(self):
        if not True:
            pass


        view_w = SCREEN_WIDTH / max(1e-6, self.zoom_level)
        view_h = SCREEN_HEIGHT / max(1e-6, self.zoom_level)


        target_left = self.player.center_x - view_w / 2
        target_bottom = self.player.center_y - view_h / 2

        # Ограничим камеру слева и снизу (не уходим в отрицательные координаты)
        if target_left < 0:
            target_left = 0
        if target_bottom < 0:
            target_bottom = 0


        try:
            self._cam_left = float(target_left)
            self._cam_bottom = float(target_bottom)
        except Exception:
            self._cam_left = target_left
            self._cam_bottom = target_bottom

        # Устанавливаем вьюпорт с учетом зума
        try:
            arcade.set_viewport(
                int(target_left),
                int(target_left + view_w),
                int(target_bottom),
                int(target_bottom + view_h)
            )
        except Exception:

            try:
                if hasattr(self, 'camera') and self.camera:

                    if hasattr(self.camera, 'move_to'):
                        self.camera.move_to((target_left, target_bottom), 0.0)
                    else:
                        try:
                            self.camera.position = (target_left, target_bottom)
                        except Exception:
                            pass
            except Exception:
                pass

    def advance_level(self):
        next_index = self.level_index + 1
        if next_index >= len(LEVELS):
            self.state = STATE_VICTORY
        else:
            self.setup(next_index)
            self.state = STATE_GAME


    def on_update(self, delta_time):
        if self.state != STATE_GAME:
            return


        self.player.change_y -= GRAVITY

        self.player.center_y += self.player.change_y
        walls_hit = arcade.check_for_collision_with_list(self.player, self.wall_list)
        for wall in walls_hit:
            if self.player.change_y > 0:
                self.player.top = wall.bottom
            else:
                self.player.bottom = wall.top
            self.player.change_y = 0

        self.player.center_x += self.player.change_x
        walls_hit = arcade.check_for_collision_with_list(self.player, self.wall_list)
        for wall in walls_hit:
            if self.player.change_x > 0:
                self.player.right = wall.left
            else:
                self.player.left = wall.right


        for plat in self.platform_list:
            plat.center_x += plat.change_x
            left = getattr(plat, "bound_left", None)
            right = getattr(plat, "bound_right", None)
            if left is not None and right is not None:
                if plat.center_x < left or plat.center_x > right:
                    plat.change_x *= -1

        if (self.player.change_y <= 0 and
                    abs(self.player.bottom - plat.top) < 10 and
                    self.player.right > plat.left and self.player.left < plat.right):
                self.player.bottom = plat.top
                self.player.change_y = 0
                self.player.center_x += plat.change_x


        for npc in list(self.npc_list):
            npc.update()


            if arcade.check_for_collision(npc, self.player):
                now = time.time()
                if now - npc.last_hit_time > 0.8:
                    npc.last_hit_time = now

                    dmg = npc.damage if hasattr(npc, "damage") else 1
                    self.lives -= dmg
                    if self.lives > 0:
                        self.player.center_x, self.player.center_y = self.respawn_x, self.respawn_y
                        self.player.change_x = self.player.change_y = 0
                    else:
                        self.state = STATE_GAME_OVER

        for proj in list(self.projectile_list):

            proj.center_x += proj.change_x
            proj.center_y += proj.change_y

            if time.time() - getattr(proj, "spawn_time", 0) > getattr(proj, "lifetime", 2.5):
                try:
                    proj.remove_from_sprite_lists()
                except Exception:
                    pass
                continue

            hits = arcade.check_for_collision_with_list(proj, self.npc_list)
            for h in hits:

                h.hp -= 1

                try:
                    proj.remove_from_sprite_lists()
                except Exception:
                    pass

                if h.hp <= 0:

                    exp_tex = LEVELS[self.level_index].get("exp_texture")
                    if exp_tex and os.path.exists(os.path.join(PATH, exp_tex)):
                        try:
                            sphere = arcade.Sprite(os.path.join(PATH, exp_tex))
                            sphere.width = 20
                            sphere.height = 20
                        except Exception:
                            sphere = arcade.SpriteSolidColor(20, 20, arcade.color.GOLD)
                    else:
                        sphere = arcade.SpriteSolidColor(20, 20, arcade.color.GOLD)
                    sphere.center_x, sphere.center_y = h.center_x, h.center_y
                    sphere.value = 5
                    self.exp_list.append(sphere)


                    try:
                        h.remove_from_sprite_lists()
                    except Exception:
                        pass


                    if h.is_boss:

                        self.state = STATE_VICTORY
                        return

                break


        if self.player_textures:
            if self.player.change_x > 0:
                self.player_facing = "right"
            elif self.player.change_x < 0:
                self.player_facing = "left"

            if abs(self.player.change_y) > 0.5:
                tex = self.player_textures[self.player_facing].get("jump")
                if tex:
                    self.player.texture = tex
            elif abs(self.player.change_x) > 0.1:
                self.animation_timer += delta_time
                if self.animation_timer >= self.animation_interval:
                    self.animation_timer = 0.0
                    self.walk_frame = 1 - self.walk_frame
                if self.walk_frame == 0:
                    tex = self.player_textures[self.player_facing].get("stand")
                else:
                    tex = self.player_textures[self.player_facing].get("walk")
                if tex:
                    self.player.texture = tex
            else:
                tex = self.player_textures[self.player_facing].get("stand")
                if tex:
                    self.player.texture = tex
                self.animation_timer = 0.0
                self.walk_frame = 0

        exp_hit = arcade.check_for_collision_with_list(self.player, self.exp_list)
        for exp in exp_hit:
            try:
                val = getattr(exp, "value", 5)
                exp.remove_from_sprite_lists()
            except Exception:
                val = 5
            self.exp_score += int(val)

        # Подбор специальных предметов (повязка Цезаря и др.)
        special_hit = arcade.check_for_collision_with_list(self.player, self.special_item_list)
        for item in special_hit:
            try:
                if getattr(item, "item_name", "") == "caesar_band":
                    self.has_caesar = True
                item.remove_from_sprite_lists()
            except Exception:
                pass

        if len(self.exp_list) == 0:
            for t in list(self.transition_list):
                if getattr(t, "locked", True):
                    t.locked = False
                    unlocked = LEVELS[self.level_index].get("transition_unlocked")
                    if unlocked and os.path.exists(os.path.join(PATH, unlocked)):
                        try:
                            t.texture = arcade.load_texture(os.path.join(PATH, unlocked))
                        except Exception:
                            pass
                    else:
                        try:

                            new_t = arcade.SpriteSolidColor(getattr(t, "width", 48) or 48,
                                                            getattr(t, "height", 64) or 64,
                                                            arcade.color.GREEN)
                            new_t.center_x, new_t.center_y = t.center_x, t.center_y
                            new_t.locked = False
                            self.transition_list[self.transition_list.index(t)] = new_t
                        except Exception:
                            t.locked = False


        if self.transition_list:
            hits = arcade.check_for_collision_with_list(self.player, self.transition_list)
            for t in hits:
                if not getattr(t, "locked", True):
                    self.advance_level()
                    return


        if self.player.center_y < -100:
            self.lives -= 1
            if self.lives > 0:
                self.player.center_x, self.player.center_y = self.respawn_x, self.respawn_y
                self.player.change_x = self.player.change_y = 0
            else:
                self.state = STATE_GAME_OVER

        self.scroll_to_player()


    def on_key_press(self, key, modifiers):
        if self.state == STATE_MENU:
            if key == arcade.key.ENTER:
                self.setup(0)
                self.state = STATE_GAME
            return

        if self.state == STATE_VICTORY:
            if key == arcade.key.ENTER:
                self.state = STATE_MENU
            return

        if self.state == STATE_GAME_OVER:
            if key == arcade.key.R:
                self.setup(self.level_index)
                self.state = STATE_GAME
            return

        if self.state == STATE_GAME:
            if key in (arcade.key.UP, arcade.key.W, arcade.key.SPACE):
                if abs(self.player.change_y) < 0.1:
                    self.player.change_y = JUMP_SPEED
            elif key in (arcade.key.LEFT, arcade.key.A):
                self.player.change_x = -MOVEMENT_SPEED
            elif key in (arcade.key.RIGHT, arcade.key.D):
                self.player.change_x = MOVEMENT_SPEED
            elif key == arcade.key.Z:
                self.zoom_level = max(0.3, round(self.zoom_level - 0.1, 2))
            elif key == arcade.key.X:
                self.zoom_level = min(3.0, round(self.zoom_level + 0.1, 2))
            elif key == arcade.key.COMMA:  # ',' decrease volume
                self.music_volume = max(0.0, round(self.music_volume - 0.05, 2))
                self.music_muted = (self.music_volume == 0.0)
                self._update_music_volume()
            elif key == arcade.key.PERIOD:  # '.' increase
                self.music_volume = min(1.0, round(self.music_volume + 0.05, 2))
                if self.music_volume > 0.0:
                    self.music_muted = False
                self._update_music_volume()
            elif key == arcade.key.M:
                self.music_muted = not self.music_muted
                self._update_music_volume()

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D):
            self.player.change_x = 0

    def on_mouse_press(self, x, y, button, modifiers):

        if self.state != STATE_GAME:
            return
        if button == arcade.MOUSE_BUTTON_LEFT and self.has_caesar:

            if self.exp_score < 1:
                return
            now = time.time()
            if now - self._last_shot_time < self.shoot_cooldown:
                return
            self._last_shot_time = now

            self.exp_score -= 1


            try:
                cam_left = self._cam_left
                cam_bottom = self._cam_bottom
            except Exception:
                view_w = SCREEN_WIDTH / max(1e-6, self.zoom_level)
                view_h = SCREEN_HEIGHT / max(1e-6, self.zoom_level)
                cam_left = self.player.center_x - view_w / 2
                cam_bottom = self.player.center_y - view_h / 2


            world_x = cam_left + (x / max(1e-6, self.zoom_level))
            world_y = cam_bottom + (y / max(1e-6, self.zoom_level))

            dx = world_x - self.player.center_x
            dy = world_y - self.player.center_y
            dist = math.hypot(dx, dy) or 1.0
            speed = 12.0
            vx = dx / dist * speed
            vy = dy / dist * speed
            proj = create_projectile(self.projectile_texture, self.player.center_x, self.player.center_y, vx, vy, lifetime=2.5)
            self.projectile_list.append(proj)


if __name__ == "__main__":
    window = GameWindow()
    arcade.run()
