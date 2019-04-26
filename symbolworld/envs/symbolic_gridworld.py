"""A scrolling maze to explore. Collect all of the coins!

The goal of the this environment is to test generalization and symbol extraction for planning.


Todo list: (Ordered by importance)

# TODO(!!!)  Objective generator
    Generate a graph of objectives. Such as keys, doors, multiple keys for different doors.

# TODO(!!!)  Objective solver
    We need a deterministic solver to confirm that this map is actually solvable before dispatching to agent


# TODO(!!)  Dynamics objects
    Objects change shape, color per round

# TODO(!!)  Dynamic map size / walls

# TODO(!!)  OpenAI GyM Compatibility

# TODO(!!)  Dynamic background

# TODO(!)   Partial Viewport



Better Scrolly Maze is better than Scrolly Maze because it uses a much simpler
scrolling mechanism: cropping! As far as the pycolab engine is concerned, the
game world doesn't scroll at all: it just renders observations that are the size
of the entire map. Only later do "cropper" objects crop out a part of the
observation to give the impression of a moving world.

This cropping mechanism also makes it easier to derive multiple observations
from the same game, so the human user interface shows three views of the map at
once: a moving view that follows the player, another one that follows the
Patroller Sprite identified by the 'c' character, and a third that remains fixed
on a tantalisingly large hoard of gold coins, tempting the player to explore.

Regrettably, the cropper approach does mean that we have to give up the cool
starfield floating behind the map in Scrolly Maze. If you like the starfield a
lot, then Better Scrolly Maze isn't actually better.

Command-line usage: `better_scrolly_maze.py <level>`, where `<level>` is an
optional integer argument selecting Better Scrolly Maze levels 0, 1, or 2.

Keys: up, down, left, right - move. q - quit.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from enum import IntEnum
import sys

from PyQt5.QtCore import Qt
import numpy as np
import gym
from gym import spaces

from pycolab import ascii_art
from pycolab import cropping
from pycolab import human_ui_qt
from pycolab import things as plab_things
from pycolab.prefab_parts import sprites as prefab_sprites
from pycolab.plot import Plot
from pycolab.level_generator import generate_level
from pycolab.config import *


def make_game(init_board):
    """Builds and returns a Better Scrolly Maze game for the selected level."""

    return ascii_art.ascii_art_to_game(
        init_board, what_lies_beneath=' ',
        sprites={
            'P': PlayerSprite,
            'a': PatrollerSprite,
        },
        drapes={
            'K': KeyDrape,
            '@': GoalDrape},
        update_schedule=['a', 'K', 'P', '@'],
        z_order='aK@P')

class PlayerSprite(prefab_sprites.LargerObject):
    """A `Sprite` for our player, the maze explorer."""

    def __init__(self, corner, position, character):
        """Constructor: just tells `MazeWalker` we can't walk through walls."""
        color = get_color('sprite')
        # Example of a 5 x 5 diamond, Key: relative position to center, Value: RGB value
        img = {(-2, 0): color,
               (-1, -1): color,
               (-1, 1): color,
               (0, -2): color,
               (0,0):color,
               (0, 2): color,
               (1, -1): color,
               (1, 1): color,
               (2, 0): color,
               (0, 1): color,
               (0, -1): color,
               (-1, 0): color,
               (1, 0): color,
               }
        super(PlayerSprite, self).__init__(
            img, corner, position, character, impassable='#')

    def update(self, actions, board, layers, backdrop, things, the_plot):
        del backdrop, things, layers  # Unused

        if actions == 0:  # go upward?
            self._north(board, the_plot)
        elif actions == 1:  # go downward?
            self._south(board, the_plot)
        elif actions == 2:  # go leftward?
            self._west(board, the_plot)
        elif actions == 3:  # go rightward?
            self._east(board, the_plot)
        elif actions == 4:  # stay put? (Not strictly necessary.)
            self._stay(board, the_plot)
        if actions == 5:  # just quit?
            the_plot.terminate_episode()

class PatrollerSprite(prefab_sprites.LargerObject):
    """Wanders back and forth horizontally, killing the player on contact."""

    def __init__(self, corner, position, character):
        """Constructor: list impassables, initialise direction."""

        color = get_color('patroller')
        # Example of a 5 x 5 diamond, Key: relative position to center, Value: RGB value
        img = {(-2, 0): color,
               (-1, -1): color,
               (-1, 1): color,
               (0, -2): color,
               (0,0):color,
               (0, 2): color,
               (1, -1): color,
               (1, 1): color,
               (2, 0): color,
               }
        super(PatrollerSprite, self).__init__(
            img, corner, position, character, impassable='#')
        # Choose our initial direction based on our character value.
        self._moving_east = False

    def update(self, actions, board, layers, backdrop, things, the_plot):
        del actions, backdrop  # Unused.

        # We only move once every two game iterations.
        if the_plot.frame % 2:
            self._stay(board, the_plot)  # Also not strictly necessary.
            return

        # If there is a wall next to us, we ought to switch direction.
        row, col = self.position
        if layers['#'][row, col - 3]: self._moving_east = True
        if layers['#'][row, col + 3]: self._moving_east = False

        # Make our move. If we're now in the same cell as the player, it's instant
        # game over!
        (self._east if self._moving_east else self._west)(board, the_plot)
        # if self.position == things['P'].position: the_plot.terminate_episode()
        if self.is_colliding(things['P']): the_plot.terminate_episode()

class GoalDrape(plab_things.LargeDrape, plab_things.ILarge):
    """A `Drape` handling all of the coins.

    This Drape detects when a player traverses a coin, removing the coin and
    crediting the player for the collection. Terminates if all coins are gone.
    """

    def __init__(self, curtain, character):
        """Constructor: list impassables, initialise direction."""

        color = get_color('goal')
        # Example of a 5 x 5 diamond, Key: relative position to center, Value: RGB value
        img = {
                (-2, -2): color,
               (-2, -1): color,
               (-2, 0): color,
               (-2, 1): color,
               (-2, 2): color,
                (-2, 2): color,
                (-1, 2): color,
                (0, 2): color,
                (1, 2): color,
                (2, 2): color,
                (2, 1): color,
                (2, 0): color,
                (2, -1): color,
                (-1, -2): color,
                (0, -2): color,
                (1, -2): color,
                (2, -2): color,
               }
        super(GoalDrape, self).__init__(
            img, curtain, character)

    def update(self, actions, board, layers, backdrop, things, the_plot):
        # If the player has reached a coin, credit one reward and remove the coin
        # from the scrolling pattern. If the player has obtained all coins, quit!
        player_pattern_position = things['P'].position

        for drape_coord in self.drape_list:
            if self.is_colliding(things['P'], drape_coord) \
                    and 'key_count' in the_plot.keys() \
                    and the_plot['key_count'] > 0:

                the_plot['key_count'] -= 1
                the_plot.log('Goal reached at {}!'.format(player_pattern_position))
                the_plot.add_reward(100)
                self.curtain[drape_coord[0], drape_coord[1]] = False
                if not self.curtain.any(): the_plot.terminate_episode()
                break

class KeyDrape(plab_things.LargeDrape, plab_things.ILarge):
    """A `Drape` handling all of the keys.

    A key is needed to unlock the goal
    """
    def __init__(self, curtain, character):
        """Constructor: list impassables, initialise direction."""
        color = get_color('key')
        img = {
            (-1, -2): color,
            (-1, -1): color,
            (-1, 0): color,
            (-1, 1): color,
            (-1, 2): color,
            (-1, 3): color,
            (0, -3): color,
            (0, -1): color,
            (0, 1): color,
            (0, 3): color,
            (1, -2): color,
            (1, 1): color,
            (1, 3): color,
               }

        super(KeyDrape, self).__init__(
            img, curtain, character)

    def update(self, actions, board, layers, backdrop, things, the_plot: Plot):
        # If the player has reached a coin, credit one reward and remove the coin
        # from the scrolling pattern. If the player has obtained all coins, quit!
        player_pattern_position = things['P'].position

        for drape_coord in self.drape_list:
            if self.is_colliding(things['P'], drape_coord):
                the_plot.log('Key collected at {}!'.format(player_pattern_position))
                the_plot.add_reward(100)

                if 'key_count' not in the_plot:
                    the_plot['key_count'] = 0
                the_plot['key_count'] += 1

                self.curtain[drape_coord[0], drape_coord[1]] = False
                break

class SimpleSymbolWorldEnv(gym.Env):
    ''' Simple Gym wrapper for the PyColab environment '''


    metadata = {
        'render.modes': ['human', 'rgb_array', 'pixmap'],
        'video.frames_per_second' : 10
    }

    # Enumeration of possible actions
    class Actions(IntEnum):
        # Turn left, turn right, move forward
        up = 0
        down = 1
        left = 2
        right = 3

        # Drop an object
        stay = -1


    def __init__(self):
        self.actions = SimpleSymbolWorldEnv.Actions
        self.action_space = spaces.Discrete(len(self.actions))

        self.observation_space = spaces.Dict({
            'image': spaces.Box(
                low=0,
                high=255,
                shape=(GRID_SIZE, GRID_SIZE, 3),
                dtype='uint8'
            )
        })

        # Range of possible rewards
        self.reward_range = (0, 1)
        self.reset()
        self.human_ui = human_ui_qt.HumanUI(
        rows=GRID_SIZE,
        cols=GRID_SIZE,

        keys_to_actions={Qt.Key_Up: 0, Qt.Key_Down: 1,
                         Qt.Key_Left: 2, Qt.Key_Right: 3,
                         -1: 4,
                         Qt.Key_Q: 5},
        delay=100,
        # croppers=level
    )

    def step(self, action):

        obs, reward, discount_factor = self._game_engine.play(action)
        self.obs = obs
        return obs, reward, self._game_engine.game_over, None

    def reset(self):
        reset_colors()
        init_gameboard = generate_level()
        self._game_engine = make_game(init_gameboard)
        self.obs, _, _ = self._game_engine.its_showtime()

        pass

    def render(self, mode='rgb_array'):
        if mode == 'rgb_array':
            return self.obs

        elif mode == 'human':
            return self.human_ui.display([self.obs], 0, 0) # quirk in obs, original display takes cropper



_color_map = {}
def get_color(object_name):
    ''' Generate / retrives a color for a group of entities '''
    if object_name not in _color_map:
        color = np.random.randint(0, 256, size=3)  # RGB
        _color_map[object_name] = color

    return _color_map[object_name]

def reset_colors():
    '''Resets color map, used for when a round resets'''
    global _color_map
    _color_map = {}

def main(argv=()):

    # Build a Better Scrolly Maze game.
    init_gameboard = generate_level()
    game = make_game(init_gameboard)

    rows = len(LEVEL)
    cols = len(LEVEL[0])
    # Make a CursesUi to play it with.
    ui = human_ui_qt.HumanUI(
        rows=rows,
        cols=cols,

        keys_to_actions={Qt.Key_Up: 0, Qt.Key_Down: 1,
                         Qt.Key_Left: 2, Qt.Key_Right: 3,
                         -1: 4,
                         Qt.Key_Q: 5},
        delay=100,
        # croppers=level
    )

    # Let the game begin!
    ui.play(game)


if __name__ == '__main__':
    main(sys.argv)
