import arcade
import random
import math
import sqlite3
import os

SCREEN_WIDTH = 2048
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Project"
PLAYER_MOVEMENT_SPEED = 20
METEORITE_SCALE = 0.15
DEFAULT_BULLET_SPEED = 15
BULLET_LIFETIME = 2.0
BASE_METEORITE_SPAWN_RATE = 2.0
DEFAULT_METEORITE_SPEED = 8
PLAYER_MAX_HITS = 3
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"
SCORE_SPEED_BONUS_THRESHOLD = 100
MAX_SPEED_BONUS = 1.0
SECRET_MESSAGE_X_OFFSET = 500
SECRET_MESSAGE = "by tamerlan"
SECRET_MESSAGE_COLOR = arcade.color.GOLD
PARTICLE_COUNT = 15
PARTICLE_MIN_SPEED = 2
PARTICLE_MAX_SPEED = 8
PARTICLE_LIFETIME = 1.0
PARTICLE_COLORS = [
    arcade.color.ORANGE,
    arcade.color.YELLOW,
    arcade.color.RED,
    arcade.color.WHITE
]
DB_FILE = "high_scores.db"
NEW_RECORD_DISPLAY_TIME = 1.0


class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS high_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                difficulty TEXT NOT NULL,
                score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def get_high_score(self, difficulty):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT score FROM high_scores 
            WHERE difficulty = ? 
            ORDER BY score DESC 
            LIMIT 1
        ''', (difficulty,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def save_score(self, difficulty, score):
        current_high = self.get_high_score(difficulty)
        if score > current_high:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO high_scores (difficulty, score) 
                VALUES (?, ?)
            ''', (difficulty, score))
            conn.commit()
            conn.close()
            return True
        return False

    def get_all_high_scores(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT difficulty, MAX(score) as max_score 
            FROM high_scores 
            GROUP BY difficulty
        ''')
        results = cursor.fetchall()
        conn.close()
        high_scores = {}
        for difficulty, score in results:
            high_scores[difficulty] = score
        return high_scores


class Particle(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.texture = arcade.make_circle_texture(10, random.choice(PARTICLE_COLORS))
        self.scale = random.uniform(0.2, 0.5)
        self.center_x = x
        self.center_y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(PARTICLE_MIN_SPEED, PARTICLE_MAX_SPEED)
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.lifetime = PARTICLE_LIFETIME
        self.initial_lifetime = PARTICLE_LIFETIME
        self.fade_rate = 1.0 / PARTICLE_LIFETIME

    def update(self, delta_time: float = 1 / 60):
        super().update()
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()
            return
        alpha = int(255 * (self.lifetime / self.initial_lifetime))
        if alpha < 0:
            alpha = 0
        self.color = (self.color[0], self.color[1], self.color[2], alpha)
        self.change_x *= 0.98
        self.change_y *= 0.98
        self.change_y -= 0.1


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager(DB_FILE)
        self.high_scores = self.db_manager.get_all_high_scores()
        self.background_color = arcade.color.BLUE_GRAY
        self.selected_difficulty = 0
        self.difficulties = [
            (DIFFICULTY_EASY, "Легкая", arcade.color.GREEN),
            (DIFFICULTY_MEDIUM, "Средняя", arcade.color.YELLOW),
            (DIFFICULTY_HARD, "Сложная", arcade.color.RED)
        ]
        self.camera_offset = 0
        self.secret_visible = False

    def update_high_scores(self):
        self.high_scores = self.db_manager.get_all_high_scores()

    def on_draw(self):
        self.clear()
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                SCREEN_WIDTH // 2 - self.camera_offset,
                SCREEN_HEIGHT // 2,
                SCREEN_WIDTH,
                SCREEN_HEIGHT
            ),
            self.background_color
        )
        arcade.draw_text("Space Attack",
                         SCREEN_WIDTH // 2 - self.camera_offset,
                         SCREEN_HEIGHT - 100,
                         arcade.color.WHITE,
                         font_size=50,
                         anchor_x="center",
                         bold=True)
        arcade.draw_text("Лучшие результаты:",
                         SCREEN_WIDTH // 2 - self.camera_offset + 500,
                         SCREEN_HEIGHT - 180,
                         arcade.color.GOLD,
                         font_size=30,
                         anchor_x="center")
        y_pos = SCREEN_HEIGHT - 220
        for difficulty_id, name, color in self.difficulties:
            score = self.high_scores.get(difficulty_id, 0)
            arcade.draw_text(f"{name}: {score} очков",
                             SCREEN_WIDTH // 2 - self.camera_offset + 500,
                             y_pos,
                             color,
                             font_size=24,
                             anchor_x="center")
            y_pos -= 40
        arcade.draw_text("Выберите сложность:",
                         SCREEN_WIDTH // 2 - self.camera_offset,
                         SCREEN_HEIGHT // 2 + 100,
                         arcade.color.WHITE,
                         font_size=30,
                         anchor_x="center")
        for i, (difficulty_id, name, color) in enumerate(self.difficulties):
            y_pos = SCREEN_HEIGHT // 2 - i * 60
            if i == self.selected_difficulty:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(SCREEN_WIDTH // 2 - self.camera_offset, y_pos, 400, 50),
                    arcade.color.LIGHT_GRAY
                )
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(SCREEN_WIDTH // 2 - self.camera_offset, y_pos, 400, 50),
                    arcade.color.WHITE,
                    3
                )
            arcade.draw_text(name,
                             SCREEN_WIDTH // 2 - self.camera_offset,
                             y_pos,
                             color,
                             font_size=28,
                             anchor_x="center")
        arcade.draw_text("Используйте W/S или ↑/↓ для выбора",
                         SCREEN_WIDTH // 2 - self.camera_offset,
                         SCREEN_HEIGHT // 2 - 300,
                         arcade.color.WHITE,
                         font_size=20,
                         anchor_x="center")
        arcade.draw_text("Нажмите SPACE для начала игры",
                         SCREEN_WIDTH // 2 - self.camera_offset,
                         SCREEN_HEIGHT // 2 - 340,
                         arcade.color.WHITE,
                         font_size=20,
                         anchor_x="center")
        arcade.draw_text("Нажмите ESC для выхода",
                         SCREEN_WIDTH // 2 - self.camera_offset,
                         SCREEN_HEIGHT // 2 - 380,
                         arcade.color.WHITE,
                         font_size=20,
                         anchor_x="center")
        arcade.draw_text("Нажмите C для сброса всех рекордов",
                         SCREEN_WIDTH // 2 - self.camera_offset,
                         SCREEN_HEIGHT // 2 - 420,
                         arcade.color.LIGHT_GRAY,
                         font_size=18,
                         anchor_x="center")
        if self.secret_visible:
            secret_x = SCREEN_WIDTH // 2 - self.camera_offset - 600
            arcade.draw_rect_filled(
                arcade.rect.XYWH(secret_x, SCREEN_HEIGHT // 2, 400, 100),
                arcade.color.DARK_SLATE_GRAY
            )
            arcade.draw_rect_outline(
                arcade.rect.XYWH(secret_x, SCREEN_HEIGHT // 2, 400, 100),
                SECRET_MESSAGE_COLOR,
                3)
            arcade.draw_text(SECRET_MESSAGE,
                             secret_x,
                             SCREEN_HEIGHT // 2,
                             SECRET_MESSAGE_COLOR,
                             font_size=36,
                             anchor_x="center",
                             bold=True)
            arcade.draw_text("Секретная пасхалка!",
                             secret_x,
                             SCREEN_HEIGHT // 2 - 40,
                             arcade.color.LIGHT_GRAY,
                             font_size=20,
                             anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W or key == arcade.key.UP:
            self.selected_difficulty = (self.selected_difficulty - 1) % len(self.difficulties)
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.selected_difficulty = (self.selected_difficulty + 1) % len(self.difficulties)
        elif key == arcade.key.SPACE:
            difficulty_id, difficulty_name, _ = self.difficulties[self.selected_difficulty]
            game_view = GameView(difficulty_id, difficulty_name, self.db_manager)
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.A:
            self.camera_offset = -SECRET_MESSAGE_X_OFFSET
            self.secret_visible = True
        elif key == arcade.key.D:
            self.camera_offset = 0
            self.secret_visible = False
        elif key == arcade.key.C:
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            self.db_manager = DatabaseManager(DB_FILE)
            self.update_high_scores()


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.background_texture = arcade.load_texture("ddd.png")

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background_texture,
                                 arcade.rect.XYWH(self.width // 2, self.height // 2, self.width, self.height))
        arcade.draw_text("Пауза",
                         self.window.width / 2,
                         self.window.height / 2 + 100,
                         arcade.color.WHITE,
                         font_size=40,
                         anchor_x="center")
        arcade.draw_text("Сложность: " + self.game_view.difficulty_name,
                         self.window.width / 2,
                         self.window.height / 2 + 50,
                         self.game_view.difficulty_color,
                         font_size=30,
                         anchor_x="center")
        arcade.draw_text(f"Очки: {self.game_view.score}",
                         self.window.width / 2,
                         self.window.height / 2,
                         arcade.color.WHITE,
                         font_size=30,
                         anchor_x="center")
        arcade.draw_text(f"Лучший счет: {self.game_view.db_manager.get_high_score(self.game_view.difficulty_id)}",
                         self.window.width / 2,
                         self.window.height / 2 - 50,
                         arcade.color.LIGHT_BLUE,
                         font_size=25,
                         anchor_x="center")
        arcade.draw_text("Нажми SPACE, чтобы продолжить",
                         self.window.width / 2,
                         self.window.height / 2 - 180,
                         arcade.color.WHITE,
                         font_size=20,
                         anchor_x="center")
        arcade.draw_text("M чтобы выйти в главное меню",
                         self.window.width / 2,
                         self.window.height / 2 - 100,
                         arcade.color.WHITE,
                         font_size=20,
                         anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.window.show_view(self.game_view)
        elif key == arcade.key.M:
            menu_view = MenuView()
            self.window.show_view(menu_view)


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__("41.png")
        self.scale = 0.5
        self.center_x = 100
        self.center_y = SCREEN_HEIGHT // 2
        self.angle = 90
        self.shoot_timer = 0
        self.hits = 0
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.hit_animation_timer = 0
        self.visible = True


class Meteorite(arcade.Sprite):
    def __init__(self, speed_multiplier=1.0, max_hits=3):
        super().__init__('meteorite.png', METEORITE_SCALE)
        self.center_x = SCREEN_WIDTH + 50
        self.center_y = random.randint(50, SCREEN_HEIGHT - 50)
        self.change_x = -DEFAULT_METEORITE_SPEED * speed_multiplier
        self.change_y = 0
        self.angle = 0
        self.change_angle = 0
        self.hits = 0
        self.max_hits = max_hits
        self.hit_animation_timer = 0
        self.color = arcade.color.WHITE

    def update(self, delta_time: float = 1 / 60):
        super().update()
        if self.hit_animation_timer > 0:
            self.hit_animation_timer -= delta_time


class Bullet(arcade.Sprite):
    def __init__(self, x, y, speed_multiplier=1.0):
        super().__init__()
        self.texture = arcade.make_soft_square_texture(20, arcade.color.RED, 255, 255)
        self.scale = 0.1
        self.width = 50
        self.height = 3
        self.center_x = x + 30
        self.center_y = y
        self.angle = 0
        self.change_x = DEFAULT_BULLET_SPEED * speed_multiplier
        self.change_y = 0
        self.lifetime = BULLET_LIFETIME
        self.hit_meteorites = []

    def update(self, delta_time: float = 1 / 60):
        super().update()


class GameView(arcade.View):
    def __init__(self, difficulty_id, difficulty_name, db_manager):
        super().__init__()
        self.difficulty_id = difficulty_id
        self.difficulty_name = difficulty_name
        self.db_manager = db_manager
        self.is_new_record = False
        self.new_record_timer = 0.0
        if difficulty_id == DIFFICULTY_EASY:
            self.difficulty_color = arcade.color.GREEN
            self.base_meteorite_speed_multiplier = 1.0
            self.meteorite_frequency_multiplier = 2.0
            self.bullet_speed_multiplier = 1.0
            self.bullet_frequency_multiplier = 1.0
            self.meteorite_max_hits = 3
        elif difficulty_id == DIFFICULTY_MEDIUM:
            self.difficulty_color = arcade.color.YELLOW
            self.base_meteorite_speed_multiplier = 1.5
            self.meteorite_frequency_multiplier = 3.0
            self.bullet_speed_multiplier = 2.0
            self.bullet_frequency_multiplier = 2.0
            self.meteorite_max_hits = 3
        else:
            self.difficulty_color = arcade.color.RED
            self.base_meteorite_speed_multiplier = 2.0
            self.meteorite_frequency_multiplier = 4.0
            self.bullet_speed_multiplier = 4.0
            self.bullet_frequency_multiplier = 4.0
            self.meteorite_max_hits = 5
        self.speed_bonus = 0.0
        self.current_meteorite_speed_multiplier = self.base_meteorite_speed_multiplier
        self.last_bonus_score = 0
        self.meteorite_spawn_rate = BASE_METEORITE_SPAWN_RATE / self.meteorite_frequency_multiplier
        self.background_texture = arcade.load_texture("ddd.png")
        self.player = Player()
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.meteorite_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.meteorite_timer = 0
        self.total_time = 0
        self.player_health = PLAYER_MAX_HITS
        self.score = 0

    def create_explosion_particles(self, x, y):
        for _ in range(PARTICLE_COUNT):
            particle = Particle(x, y)
            self.particle_list.append(particle)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background_texture,
                                 arcade.rect.XYWH(self.width // 2, self.height // 2, self.width, self.height))
        if self.player.visible:
            self.player_list.draw()
        self.meteorite_list.draw()
        self.bullet_list.draw()
        self.particle_list.draw()

        arcade.draw_text(f"Здоровье: {self.player_health}/{PLAYER_MAX_HITS}",
                         10, SCREEN_HEIGHT - 40, arcade.color.WHITE, 24)
        arcade.draw_text(f"Счет: {self.score}",
                         10, SCREEN_HEIGHT - 80, arcade.color.WHITE, 24)
        arcade.draw_text(f"Сложность: {self.difficulty_name}",
                         10, SCREEN_HEIGHT - 120, self.difficulty_color, 24)
        arcade.draw_text(f"Попаданий для метеорита: {self.meteorite_max_hits}",
                         10, SCREEN_HEIGHT - 160, self.difficulty_color, 20)
        high_score = self.db_manager.get_high_score(self.difficulty_id)
        arcade.draw_text(f"Лучший счет: {high_score}",
                         SCREEN_WIDTH - 300, SCREEN_HEIGHT - 40, arcade.color.GOLD, 22)
        if self.is_new_record and self.new_record_timer > 0:
            alpha = int(255 * (self.new_record_timer / NEW_RECORD_DISPLAY_TIME))
            alpha = max(0, min(255, alpha))
            color_with_alpha = (arcade.color.GOLD[0], arcade.color.GOLD[1], arcade.color.GOLD[2], alpha)
            arcade.draw_text("НОВЫЙ РЕКОРД!",
                             SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT // 2,
                             color_with_alpha,
                             font_size=60,
                             anchor_x="center",
                             bold=True)

    def update_speed_bonus(self):
        bonus_count = self.score // SCORE_SPEED_BONUS_THRESHOLD
        new_bonus = min(bonus_count * 0.1, MAX_SPEED_BONUS)
        if new_bonus != self.speed_bonus:
            self.speed_bonus = new_bonus
            self.last_bonus_score = self.score - (self.score % SCORE_SPEED_BONUS_THRESHOLD)
            self.current_meteorite_speed_multiplier = self.base_meteorite_speed_multiplier + self.speed_bonus

    def on_update(self, delta_time):
        self.total_time += delta_time
        self.meteorite_timer += delta_time
        if self.is_new_record and self.new_record_timer > 0:
            self.new_record_timer -= delta_time
            if self.new_record_timer <= 0:
                self.new_record_timer = 0
        self.update_speed_bonus()
        shoot_interval = 1.0 / self.bullet_frequency_multiplier
        self.player.shoot_timer += delta_time
        if not self.is_new_record:
            high_score = self.db_manager.get_high_score(self.difficulty_id)
            if self.score > high_score:
                self.is_new_record = True
                self.new_record_timer = NEW_RECORD_DISPLAY_TIME
                self.db_manager.save_score(self.difficulty_id, self.score)
        if self.player.invulnerable:
            self.player.invulnerable_timer += delta_time
            self.player.hit_animation_timer += delta_time
            if self.player.hit_animation_timer >= 0.1:
                self.player.visible = not self.player.visible
                self.player.hit_animation_timer = 0
            if self.player.invulnerable_timer >= 2.0:
                self.player.invulnerable = False
                self.player.invulnerable_timer = 0
                self.player.hit_animation_timer = 0
                self.player.visible = True
        self.player.change_x = 0
        self.player.change_y = 0
        if self.left_pressed:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
        if self.right_pressed:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
        if self.up_pressed:
            self.player.change_y = PLAYER_MOVEMENT_SPEED
        if self.down_pressed:
            self.player.change_y = -PLAYER_MOVEMENT_SPEED
        self.player_list.update()
        if self.player.left < 0:
            self.player.left = 0
        elif self.player.right > SCREEN_WIDTH // 2:
            self.player.right = SCREEN_WIDTH // 2
        if self.player.bottom < 0:
            self.player.bottom = 0
        elif self.player.top > SCREEN_HEIGHT - 1:
            self.player.top = SCREEN_HEIGHT - 1
        if self.meteorite_timer >= self.meteorite_spawn_rate:
            meteorite = Meteorite(self.current_meteorite_speed_multiplier, self.meteorite_max_hits)
            self.meteorite_list.append(meteorite)
            self.meteorite_timer = 0
        for meteorite in self.meteorite_list:
            if meteorite.hit_animation_timer > 0:
                if int(meteorite.hit_animation_timer * 10) % 2 == 0:
                    meteorite.color = arcade.color.RED
                else:
                    meteorite.color = arcade.color.WHITE
            else:
                meteorite.color = arcade.color.WHITE
        self.meteorite_list.update(delta_time)
        if self.player.shoot_timer >= shoot_interval:
            self.shoot()
            self.player.shoot_timer = 0
        for bullet in self.bullet_list:
            bullet.lifetime -= delta_time
            if bullet.lifetime <= 0:
                bullet.remove_from_sprite_lists()
        self.bullet_list.update(delta_time)
        self.particle_list.update(delta_time)
        destroyed_meteorites = []
        for bullet in self.bullet_list:
            hit_list = arcade.check_for_collision_with_list(bullet, self.meteorite_list)
            for meteorite in hit_list:
                if meteorite not in bullet.hit_meteorites:
                    bullet.hit_meteorites.append(meteorite)
                    meteorite.hits += 1
                    meteorite.hit_animation_timer = 0.5
                    if meteorite.hits >= meteorite.max_hits:
                        destroyed_meteorites.append((meteorite.center_x, meteorite.center_y))
                        meteorite.remove_from_sprite_lists()
                        self.score += 10
                    else:
                        bullet.center_x += bullet.change_x * 2
                        bullet.center_y += bullet.change_y * 2
        for x, y in destroyed_meteorites:
            self.create_explosion_particles(x, y)
        if not self.player.invulnerable:
            player_hit_list = arcade.check_for_collision_with_list(self.player, self.meteorite_list)
            if player_hit_list:
                self.player_hit()
        for meteorite in self.meteorite_list:
            if meteorite.center_x < -100:
                meteorite.remove_from_sprite_lists()
        for bullet in self.bullet_list:
            if bullet.center_x > SCREEN_WIDTH + 100:
                bullet.remove_from_sprite_lists()

    def shoot(self):
        bullet = Bullet(self.player.center_x, self.player.center_y, self.bullet_speed_multiplier)
        self.bullet_list.append(bullet)

    def player_hit(self):
        self.player_health -= 1
        self.player.hits += 1
        self.player.invulnerable = True
        self.player.invulnerable_timer = 0
        if self.player_health <= 0:
            self.game_over()

    def game_over(self):
        self.db_manager.save_score(self.difficulty_id, self.score)
        self.player_list.clear()
        self.meteorite_list.clear()
        self.bullet_list.clear()
        self.particle_list.clear()
        menu_view = MenuView()
        self.window.show_view(menu_view)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.ESCAPE:
            pause_view = PauseView(self)
            self.window.show_view(pause_view)
        elif key == arcade.key.R:
            self.reset_game()
        elif key == arcade.key.M:
            menu_view = MenuView()
            self.window.show_view(menu_view)

    def reset_game(self):
        self.player_health = PLAYER_MAX_HITS
        self.score = 0
        self.speed_bonus = 0.0
        self.current_meteorite_speed_multiplier = self.base_meteorite_speed_multiplier
        self.last_bonus_score = 0
        self.is_new_record = False
        self.new_record_timer = 0.0
        self.player.center_x = 100
        self.player.center_y = SCREEN_HEIGHT // 2
        self.player.hits = 0
        self.player.invulnerable = False
        self.player.visible = True
        self.meteorite_list.clear()
        self.bullet_list.clear()
        self.particle_list.clear()
        self.meteorite_timer = 0
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.D:
            self.right_pressed = False


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        menu_view = MenuView()
        self.show_view(menu_view)


def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()


if __name__ == "__main__":
    main()
