import arcade

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "project"

PLAYER_MOVEMENT_SPEED = 20

class Player(arcade.Sprite):
    def __init__(self):
        super().__init__("41.png")
        self.scale = 1.0
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.w = width
        self.h = height
        self.background_texture = arcade.load_texture("ddd.png")
        self.player = Player()
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background_texture, arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h))
        self.player_list.draw()
    def on_update(self, delta_time):
        self.player.change_x = 0
        self.player.change_y = 0

        if self.left_pressed and not self.right_pressed:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
        elif self.right_pressed and not self.left_pressed:
            self.player.change_x = PLAYER_MOVEMENT_SPEED

        if self.up_pressed and not self.down_pressed:
            self.player.change_y = PLAYER_MOVEMENT_SPEED
        elif self.down_pressed and not self.up_pressed:
            self.player.change_y = -PLAYER_MOVEMENT_SPEED
        self.player_list.update()
        if self.player.left < 0:
            self.player.left = 0
        elif self.player.right > SCREEN_WIDTH - 1:
            self.player.right = SCREEN_WIDTH - 1

        if self.player.bottom < 0:
            self.player.bottom = 0
        elif self.player.top > SCREEN_HEIGHT - 1:
            self.player.top = SCREEN_HEIGHT - 1

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.D:
            self.right_pressed = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.D:
            self.right_pressed = False


def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()


if __name__ == "__main__":
    main()
