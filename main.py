"""
Platformer Game
"""

import sys
import os
import math
import arcade
import pyglet

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Geo-Explore"

CHARACTER_SCALING = .8
TILE_SCALING = 1
COIN_SCALING = 1
ARROW_SCALING = .8
BULLET_SPEED = 5
PLAYER_MOVEMENT_SPEED = 4.5
GRAVITY = 1
PLAYER_JUMP_SPEED = 15
SPRITE_PIXEL_SIZE = 256
GRID_PIXEL_SIZE = (SPRITE_PIXEL_SIZE * TILE_SCALING)

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
LEFT_VIEWPORT_MARGIN = 150
RIGHT_VIEWPORT_MARGIN = 150
BOTTOM_VIEWPORT_MARGIN = 50
TOP_VIEWPORT_MARGIN = 100
PLAYER_START_X = 64
PLAYER_START_Y = 64
# Game States
TITLE_SCREEN = 0
INSTRUCTIONS = 1
GAME_RUNNING = 2
GAME_OVER = 3


class MenuView(arcade.View):
    '''
    Try to display the title screen
    '''
    def __init__(self):
        super().__init__()
        self.background = None

    def on_show(self):
        self.background = arcade.load_texture("images/screens/title.png")

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        instructions_view = InstructionView()
        self.window.show_view(instructions_view)


class InstructionView(arcade.View):
    '''
    Try to display the Instruction_Screen
    '''
    def __init__(self):
        super().__init__()
        self.background = None

    def on_show(self):
        self.background = arcade.load_texture("images/screens/instructions.png")

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        game_view = MyGame()
        self.window.show_view(MyGame)


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # set background color
        arcade.set_background_color(arcade.csscolor.SKY_BLUE)

        # These are 'lists' that keep track of our sprites. Each sprite should
        # go into a list.
        self.coin_list = None
        self.wall_list = None
        self.foreground_list = None
        self.background_list = None
        self.dont_touch_list = None
        self.player_list = None
        self.enemy_list = None
        self.arrow_list = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our physics engine
        self.physics_engine = None

        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        # is game over?
        self.game_over = False
        # Keep track of the score
        self.score = 0
        # Death Tracking
        self.death = 0

        # Where is the right edge of the map?
        self.end_of_map = 0

        # Level
        self.level = 1

        # Load sounds
        self.collect_coin_sound = arcade.load_sound("sounds/coin.wav")
        self.jump_sound = arcade.load_sound("sounds/jump.wav")
        self.death = arcade.load_sound("sounds/hurt.wav")
        self.shoot = arcade.load_sound("sounds/arrow_shoot.wav")
        self.hit = arcade.load_sound("sounds/arrow_shoot.wav")

    def setup(self, level):
        """ Set up the game here. Call this function to restart the game. """

        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        # Keep track of the score
        self.score = 0

        self.death = 0

        # Create the Sprite lists
        self.player_list = arcade.SpriteList()
        self.foreground_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.arrow_list = arcade.SpriteList()

        # Set up the player, specifically placing it at these coordinates.
        self.player_sprite = arcade.Sprite("images/characters/player_standing.png",
                                           CHARACTER_SCALING)
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.player_list.append(self.player_sprite)

        # --- Load in a map from the tiled editor ---

        # Name of the layer in the file that has our platforms/walls
        platforms_layer_name = 'Platform'
        # Name of the layer that has items for pick-up
        coins_layer_name = 'Coins'
        # Name of the layer that has items for foreground
        foreground_layer_name = 'Foreground'
        # Name of the layer that has items for background
        background_layer_name = 'Background'
        # Name of the layer that has items we shouldn't touch
        dont_touch_layer_name = "Don't Touch"
        enemy_layer_name = "Enemies"

        # Map name
        map_name = f"map_level_{level}.tmx"

        # Read in the tiled map
        my_map = arcade.tilemap.read_tmx(map_name)

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = my_map.map_size.width * GRID_PIXEL_SIZE

        # -- Background
        self.background_list = arcade.tilemap.process_layer(my_map,
                                                            background_layer_name,
                                                            TILE_SCALING)

        # -- Foreground
        self.foreground_list = arcade.tilemap.process_layer(my_map,
                                                            foreground_layer_name,
                                                            TILE_SCALING)

        # -- Platforms
        self.wall_list = arcade.tilemap.process_layer(my_map,
                                                      platforms_layer_name,
                                                      TILE_SCALING)

        # -- Coins
        self.coin_list = arcade.tilemap.process_layer(my_map,
                                                      coins_layer_name,
                                                      TILE_SCALING)

        # -- Don't Touch Layer
        self.dont_touch_list = arcade.tilemap.process_layer(my_map,
                                                            dont_touch_layer_name,
                                                            TILE_SCALING)
        # Enemy Layer
        self.enemy_list = arcade.tilemap.process_layer(my_map, enemy_layer_name, CHARACTER_SCALING)

        enemy = arcade.Sprite("images/characters/enemy_hexagon.png", CHARACTER_SCALING)
        enemy.change_x = 2
        self.enemy_list.append(enemy)

        # set boundaries for the enemies
        enemy.boundary_right = SPRITE_PIXEL_SIZE * 8
        enemy.boundary_left = SPRITE_PIXEL_SIZE * 3
        enemy.change_x = 2
        self.enemy_list.append(enemy)

        # --- Other stuff
        # Set the background color
        if my_map.background_color:
            arcade.set_background_color(my_map.background_color)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                             self.wall_list,
                                                             GRAVITY)

    def on_draw(self):
        """ Render the screen. """

        # Clear the screen to the background color
        arcade.start_render()

        # Draw our sprites
        self.wall_list.draw()
        self.background_list.draw()
        self.wall_list.draw()
        self.coin_list.draw()
        self.dont_touch_list.draw()
        self.player_list.draw()
        self.foreground_list.draw()
        self.enemy_list.draw()
        self.arrow_list.draw()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(score_text, 10 + self.view_left, 10 + self.view_bottom,
                         arcade.csscolor.WHITE, 18)

        # Draw the number of player deaths
        death_text = f"Deaths:{self.death}"
        arcade.draw_text(death_text, 10 + self.view_left, 150 + self.view_bottom, arcade.csscolor.RED, 18)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_mouse_press(self, x, y, button, modifiers):
        '''
        Called whenever the mouse moves
        '''
        # Create a bullet
        bullet = arcade.Sprite("images/misc/arrow.png", ARROW_SCALING)

        # place the arrow at players current location
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y

        bullet.center_x = start_x
        bullet.center_y = start_y

        # Get from the mouse the destination location for the bullet
        # IMPORTANT! If you have a scrolling screen, you will also need
        # to add in self.view_bottom and self.view_left.
        dest_x = x
        dest_y = y

        # Do math to calculate how to get the bullet to the destination.
        # Calculation the angle in radians between the start points
        # and end points. This is the angle the bullet will travel.
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        # Angle the bullet sprite so it doesn't look like it is flying
        # sideways.
        bullet.angle = math.degrees(angle)
        print(f"Bullet angle: {bullet.angle:.2f}")

        # Taking into account the angle, calculate our change_x
        # and change_y. Velocity is how fast the bullet travels.
        bullet.change_x = math.cos(angle) * BULLET_SPEED
        bullet.change_y = math.sin(angle) * BULLET_SPEED

        # Add the bullet to the appropriate lists
        self.bullet_list.append(bullet)

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.physics_engine.update()
        # update all sprites
        self.arrow_list.update()

        # Loop  through each Arrow
        for arrow in self.arrow_list:
            hit_list = arcade.check_for_collision_with_list(arrow, self.enemy_list)
            if len(hit_list) > 0:
                arrow.remove_from_sprite_lists()
            for enemy in hit_list:
                enemy.remove_from_sprite_lists()
                self.score += 5
            if arrow.bottom > self.width or arrow.top < 0 or arrow.right < 0 or arrow.left > self.width:
                arrow.remove_from_sprite_lists()

        # See if we hit any coins
        coin_hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                             self.coin_list)

        # Loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play a sound
            arcade.play_sound(self.collect_coin_sound)
            # Add one to the score
            self.score += 1

        # Track if we need to change the viewport
        changed_viewport = False

        # Did the player fall off the map?
        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y
            self.death += 1

            # Set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed_viewport = True
            arcade.play_sound(self.death)

        # Did the player touch something they should not?
        if arcade.check_for_collision_with_list(self.player_sprite,
                                                self.dont_touch_list):
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

            # Set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed_viewport = True
            arcade.play_sound(self.death)

        # See if the user got to the end of the level
        if self.player_sprite.center_x >= self.end_of_map:
            # Advance to the next level
            self.level += 1

            # Load the next level
            self.setup(self.level)

            # Set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed_viewport = True

        if not self.game_over:
            # Move the enemies
            self.enemy_list.update()

            # Check each enemy
            for enemy in self.enemy_list:
                # If the enemy hit a wall, reverse
                if len(arcade.check_for_collision_with_list(enemy, self.wall_list)) > 0:
                    enemy.change_x *= -1
                # If the enemy hit the left boundary, reverse
                elif enemy.boundary_left is not None and enemy.left < enemy.boundary_left:
                    enemy.change_x *= -1
                # If the enemy hit the right boundary, reverse
                elif enemy.boundary_right is not None and enemy.right > enemy.boundary_right:
                    enemy.change_x *= -1
                # See if the player hit a enemy. If so, increment deaths.
                if len(arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list)) > 0:
                    self.player_sprite.center_x = PLAYER_START_X
                    self.player_sprite.center_y = PLAYER_START_Y
                    self.death += 1

        # --- Manage Scrolling ---

        # Scroll left
        left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed_viewport = True

        # Scroll right
        right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed_viewport = True

        # Scroll up
        top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed_viewport = True

        # Scroll down
        bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.player_sprite.bottom
            changed_viewport = True

        if changed_viewport:
            # Only scroll to integers. Otherwise we end up with pixels that
            # don't line up on the screen
            self.view_bottom = int(self.view_bottom)
            self.view_left = int(self.view_left)

            # Do the scrolling
            arcade.set_viewport(self.view_left,
                                SCREEN_WIDTH + self.view_left,
                                self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)


def main():
    """ Main method """
    window = MyGame()
    window.setup(window.level)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
